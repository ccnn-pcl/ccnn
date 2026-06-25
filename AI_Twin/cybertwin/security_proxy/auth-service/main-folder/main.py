from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, constr
from typing import Literal, Optional, Dict, List
import httpx
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import json
import logging
import time  # 新增：时间处理
import math  # 新增：指数运算
import re  # 新增：MAC地址格式校验辅助

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化FastAPI应用
app = FastAPI(title="授权微服务", description="处理三种授权请求", version="1.0")

# K8s客户端初始化（Pod内自动使用InClusterConfig，本地开发用kubeconfig）
try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()  # 本地开发时启用
v1 = client.CoreV1Api()

# ------------------------------
# 常量配置（新增JWT验证服务地址）
# ------------------------------
# BIGMODEL_API_KEY = "157c126907844cddac1f17580e89ef46.jIhIIurvUwI6btYV"
# BIGMODEL_CHAT_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
# BIGMODEL_MODEL = "glm-5.1"

LOCAL_LLM_CHAT_URL = "http://192.168.64.60:32568/v1/chat/completions"
LOCAL_LLM_MODEL = "qwen-3b"

NAMESPACE = "cybertwin"  # 与模型服务同一命名空间
# ConfigMap名称（K8s中存储配置的资源名）
APP_ROLE_CM = "app-role-config"       # 应用→角色映射
ROLE_PERM_CM = "role-perm-config"     # 角色→权限映射
COMMON_DEVICE_CM = "common-device-config"  # 常用设备列表
IP_LOCATION_CM = "ip-location-config" # IP→地点映射
IP_ACCESS_SCORE_CM = "ip-access-score-config" # IP→接入得分映射
# 新增：JWT验证服务地址（按你提供的配置）
JWT_VERIFY_URL =  "http://cybertwin-backend.cybertwin.svc.cluster.local:5000/jwt/verify"
# 模型调用地址（保持不变）
SENSITIVITY_MODEL_URL = "http://datainfer-service.abacmodel:80/predict_sensitivity"
MATCH_MODEL_URL = "http://matchinfer-service.abacmodel.svc.cluster.local:8000/predict"
USER_TRUST_MODEL_URL = "http://userinfer-service.abacmodel:80/evaluate"
# 超时配置（统一沿用10秒）
TIMEOUT = 10.0

# 新增：ConfigMap名称（对应新增的两个配置）
IP_CONNECTION_TYPE_CM = "ip-connection-type-config"  # IP→连接方式映射
CITY_NETWORK_RISK_CM = "city-network-risk-config"    # 城市→网络风险值映射
# 新增：敏感度减分值配置的ConfigMap
ADD_VALUE_CM = "add-value-config"  # 存储addvalue的ConfigMap
# 新增：衰减率配置的ConfigMap
DECAY_RATE_CM = "decay-rate-config"  # 存储decayrate1（密码衰减率）、decayrate2（生物特征衰减率）
# 新增：信任度加分值配置的ConfigMap
TRUST_SCORE_ADD_CM = "trust-score-add-config"  # 存储trust_score_add_value的ConfigMap

# ------------------------------
# 新增：mac/imsi白名单对应的ConfigMap名称（核心新增）
# ------------------------------
MAC_WHITELIST_CM = "mac-whitelist-config"  # 存储合法MAC地址白名单的ConfigMap
IMSI_WHITELIST_CM = "imsi-whitelist-config"  # 存储合法IMSI号码白名单的ConfigMap

# 新增：连接方式→固定得分映射（需求指定：5G=0.5，wifi=0.7，有线=0.9）
CONNECTION_SCORE_MAP = {
    "5G": 0.5,
    "wifi": 0.7,
    "有线": 1.2,
    "unknown": 0.5
}

# 新增：数据类型→格式映射（按需求定义）
CONTENT_TYPE_MAP = {
    "病史数据": "text",
    "用药记录": "text",
    "化验报告": "text",
    "手术记录": "text",
    "影像数据": "image"
}

# 允许的原始数据类型（用于校验）
ALLOWED_RAW_TYPES = set(CONTENT_TYPE_MAP.keys())

# ------------------------------
# 全局变量（核心修改）
# ------------------------------
# 初始默认值0.5，每次调用/evaluate/user-trust成功后自动更新
saved_trust_score: float = 0.5

# 新增：用户登录相关全局变量
last_pswd_login_time: Optional[float] = None  # 上次密码登录时间戳（秒）
last_bio_login_time: Optional[float] = None  # 上次生物登录时间戳（秒）
pswdold: float = 0.0  # 上次密码登录的pswd值（初始默认0.0）
bioold: float = 0.0   # 上次生物登录的bio值（初始默认0.0）
timegap_pswd: int = 0  # 密码登录时间差（分钟，四舍五入后）
timegap_bio: int = 0  # 生物登录时间差（分钟，四舍五入后）

# ====================== 仅新增：授权拒绝次数统计 ======================
deny_count: int = 0
deny_count2: int = 0
# ====================================================================

# ------------------------------
# 请求/响应数据模型（核心修改 + 新增mac/imsi请求模型）
# ------------------------------
# 1. 应用-角色-权限授权请求（保持不变）
class AppAuthRequest(BaseModel):
    app_name: str = Field(..., description="应用名称（如medicalAI）")
    data_type: str = Field(..., description="数据类型（如medical）")
    operation_type: Literal["read", "write", "delete", "update"] = Field(..., description="操作类型")

# 2. 信任度-敏感度授权请求（核心修改：仅保留token字段）
class NewTrustSensitivityAuthRequest(BaseModel):
    token: str = Field(..., description="JWT令牌（payload需包含department和type字段，type格式为'病史数据 用药记录 ...'）")

# 3. 用户信任度评估请求（核心修改：新增pswd字段）
class UserTrustRequest(BaseModel):
    ipaddress: str = Field(..., description="IP地址（如192.168.1.100）")
    time: int = Field(..., ge=0, le=23, description="访问时间（小时，0-23）")
    bio: float = Field(..., ge=0.0, le=1.0, description="生物特征匹配度（0-1）")
    device: str = Field(..., description="设备标识（如device_123、iPhone14）")
    city: str = Field(..., description="城市（如长沙）")
    # 新增pswd字段 ↓↓↓
    pswd: float = Field(..., ge=0.0, le=1.0, description="密码验证得分（0-1）")

# 4. 新增：简易敏感度授权请求模型（仅输入数据敏感度等级）
class SensitivitySimpleAuthRequest(BaseModel):
    sensitivity_score: float = Field(..., ge=0.0, description="数据敏感度等级（数值越大敏感度越高）")

# ------------------------------
# 新增：mac/imsi校验请求模型（核心新增）
# ------------------------------
class MacImsiAuthRequest(BaseModel):
    mac: str = Field(
        ...,
        description="设备MAC地址（格式如70:C9:4E:E2:FF:1B）",
        # 可选：MAC地址格式正则校验，提高接口健壮性
        pattern=r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$"
    )
    imsi: str = Field(
        ...,
        description="用户IMSI号码（格式如466920000000001）",
        # 可选：IMSI格式校验（15位数字）
        min_length=15,
        max_length=15,
        pattern=r"^\d{15}$"
    )

# 响应模型（核心修改）
class AuthResponse(BaseModel):
    result: Literal["allow", "deny"] = Field(..., description="授权结果")
    message: Optional[str] = Field(None, description="附加信息")

class TrustScoreResponse(BaseModel):
    trust_score: float = Field(..., description="用户信任度打分（0-1）")
    status: str = Field(..., description="状态（success/failed）")
    message: str = Field(..., description="描述信息")

# 新增：信任度-敏感度授权专用响应模型（替换原AuthResponse）
class TrustSensitivityAuthResponse(BaseModel):
    valid: bool = Field(..., description="授权结果（true=通过，false=拒绝/令牌无效/调用失败）")
    message: Optional[str] = Field(None, description="附加信息（错误原因/授权详情）")

# ------------------------------
# 工具函数（保持不变）
# ------------------------------
def get_configmap(cm_name: str) -> Dict[str, str]:
    """读取K8s ConfigMap数据，失败则抛异常"""
    try:
        cm = v1.read_namespaced_config_map(name=cm_name, namespace=NAMESPACE)
        return cm.data or {}
    except ApiException as e:
        logger.error(f"读取ConfigMap[{cm_name}]失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置读取失败：{cm_name}")

def parse_json_config(cm_name: str, key: str) -> Dict:
    """解析ConfigMap中JSON格式的配置（如角色权限、常用设备）"""
    cm_data = get_configmap(cm_name)
    value = cm_data.get(key)
    if not value:
        raise HTTPException(status_code=500, detail=f"ConfigMap[{cm_name}]缺少key: {key}")
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"ConfigMap[{cm_name}][{key}]格式错误（需JSON）")


def parse_sensitivity_level(model_answer: str) -> float | None:
    """
    从模型回答中提取敏感度等级数字，只接受1-5。
    例如：'5'、'5级'、'等级：5' 都可以解析为 5.0。
    """
    if not model_answer:
        return None

    match = re.search(r"[1-5]", model_answer)
    if not match:
        return None

    return float(match.group())


# ------------------------------
# 新增：辅助函数 - 从ConfigMap中提取白名单列表（核心新增）
# ------------------------------
def get_whitelist_from_cm(cm_name: str, key: str = "whitelist") -> List[str]:
    """
    从ConfigMap中提取白名单列表（支持换行/逗号分隔格式）
    :param cm_name: ConfigMap名称
    :param key: ConfigMap中存储白名单的键名
    :return: 去重、过滤空值后的白名单列表（统一转大写/去除空格，提高兼容性）
    """
    cm_data = get_configmap(cm_name)
    whitelist_str = cm_data.get(key, "")
    
    if not whitelist_str:
        logger.warning(f"ConfigMap[{cm_name}]的key[{key}]为空，返回空白名单")
        return []
    
    # 支持两种分隔格式：换行（优先）、逗号
    if "\n" in whitelist_str:
        whitelist_list = whitelist_str.split("\n")
    else:
        whitelist_list = whitelist_str.split(",")
    
    # 数据清洗：去重、过滤空值、去除首尾空格、MAC地址统一转大写（IMSI不影响）
    cleaned_whitelist = []
    for item in whitelist_list:
        cleaned_item = item.strip()
        if cleaned_item:
            # MAC地址统一转大写，提高匹配兼容性（如70:c9:4e → 70:C9:4E）
            if ":" in cleaned_item:
                cleaned_item = cleaned_item.upper()
            cleaned_whitelist.append(cleaned_item)
    
    # 去重（保持顺序）
    final_whitelist = list(dict.fromkeys(cleaned_whitelist))
    logger.info(f"从ConfigMap[{cm_name}]提取到有效白名单，共{len(final_whitelist)}条记录")
    return final_whitelist

# ------------------------------
# 核心接口实现（核心修改 + 新增mac/imsi校验接口）

@app.post("/auth/app-role", response_model=AuthResponse, summary="应用-角色-权限授权")
async def app_role_auth(request: AppAuthRequest):
    """逻辑：应用名称→角色→权限，判断是否允许操作数据"""
    # 🔥 核心修复：仅在函数最开头声明1次全局变量
    global deny_count2

    # 记录请求开始
    logger.info(f"开始处理应用授权请求 - 应用名: {request.app_name}, 数据类型: {request.data_type}, 操作类型: {request.operation_type}")
    
    # 1. 应用→角色（ConfigMap: app-role-config，key=应用名，value=角色名）
    app_role_data = get_configmap(APP_ROLE_CM)
    role = app_role_data.get(request.app_name)
    logger.info(f"从配置中获取应用[{request.app_name}]对应的角色: {role}")
    
    if not role:
        deny_msg = f"应用[{request.app_name}]未配置角色"
        logger.info(f"授权失败: {deny_msg}")
        deny_count2 +=1  # 直接使用，无需重复写global
        return AuthResponse(result="deny", message=deny_msg)
    
    # 2. 校验角色不存在于 role-perm-config 的key中 → 无任何权限，直接拒绝
    role_perm_config = get_configmap(ROLE_PERM_CM)
    if role not in role_perm_config:
        deny_msg = f"角色[{role}]不存在于权限配置role-perm-config中，无任何操作权限"
        logger.info(f"授权失败: {deny_msg}")
        deny_count2 +=1  # 直接使用
        return AuthResponse(result="deny", message=deny_msg)
    
    # 3. 角色→权限解析（ConfigMap: role-perm-config，key=角色名，value=JSON{"数据类型": ["操作列表"]}）
    role_perm = parse_json_config(ROLE_PERM_CM, role)
    allowed_ops = role_perm.get(request.data_type, [])
    logger.info(f"角色[{role}]拥有的{request.data_type}类型权限: {allowed_ops}")
    
    # 4. 权限校验
    if request.operation_type in allowed_ops:
        allow_msg = f"授权通过：应用[{request.app_name}]（角色[{role}]）拥有{request.data_type}:{request.operation_type}权限"
        logger.info(f"授权成功: {allow_msg}")
        return AuthResponse(
            result="allow",
            message=allow_msg
        )
    else:
        deny_msg = f"授权拒绝：应用[{request.app_name}]缺少{request.data_type}:{request.operation_type}权限"
        logger.info(f"授权失败: {deny_msg}")
        deny_count2 +=1  # 直接使用
        return AuthResponse(
            result="deny",
            message=deny_msg
        )

# ====================== 【新增】外部 ABAC 接口调用工具函数 ======================
# ====================== 【最终版】ABAC 接口调用 ======================
async def call_abac_api(result: bool, user_id: str):
    """
    调用外部ABAC接口
    :param result: 授权结果 True/False
    :param user_id: 从JWT获取的真实用户ID
    """
    url = "http://192.168.193.12:30050/abac"
    result_str = "True" if result else "False"

    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                params={
                    "result": result_str,
                    "user_id": user_id  # 真实用户ID
                },
                timeout=2.0
            )
        logger.info(f"✅ ABAC API 调用成功：result={result_str}, user_id={user_id}")
    except Exception as e:
        logger.warning(f"⚠️ ABAC API 调用失败（不影响主流程）：{e}")



# 全局缓存：存储 token -> { "time": 时间, "valid": 上次结果 }
_REQUEST_CACHE: Dict[str, dict] = {}
CACHE_WINDOW = 10  # 秒

@app.post(
    "/auth/trust-sensitivity", 
    response_model=TrustSensitivityAuthResponse,
    summary="信任度-敏感度授权"
)
async def trust_sensitivity_auth(request: NewTrustSensitivityAuthRequest):
    # ====================== 核心防重复执行（10秒内同一个token只跑一次） ======================
    token = request.token
    now = time.time()

    # 10秒内重复直接返回，不执行任何业务、不调用ABAC
    if token in _REQUEST_CACHE:
        cache_data = _REQUEST_CACHE[token]
        # 10秒内重复：直接返回上次真实结果
        if now - cache_data["time"] < CACHE_WINDOW:
            last_valid = cache_data["valid"]
            logger.info(f"✅ 重复请求已拦截，返回上次授权结果：valid={last_valid}，token={token[:20]}...")
            return TrustSensitivityAuthResponse(
                valid=last_valid,  # 关键：返回上次真实结果，不写死 True
                message="重复请求已过滤，返回上次授权结果"
            )

    # ====================== 防重结束 ======================

    async with httpx.AsyncClient() as client:
        logger.info(f"开始处理信任度-敏感度授权请求，使用保存的信任度：{saved_trust_score}")
        try:
            jwt_resp = await client.post(
                JWT_VERIFY_URL,
                json={"token": request.token},
                timeout=TIMEOUT
            )
            jwt_resp.raise_for_status()
            jwt_data = jwt_resp.json()
            logger.info(f"JWT验证服务返回结果：{jwt_data}")
        except httpx.RequestError as e:
            logger.error(f"调用JWT验证服务失败：{e}")
            global deny_count
            deny_count +=1
            #await call_abac_api(False, "unknown_user")
            return TrustSensitivityAuthResponse(
                valid=False,
                message="JWT验证服务不可用，请稍后重试"
            )
        
        if not jwt_data.get("valid", False):
            error_msg = jwt_data.get("error", "未知错误")
            logger.warning(f"JWT令牌无效：{error_msg}，令牌：{request.token[:20]}...")
            deny_count +=1
            #await call_abac_api(False, "unknown_user")
            return TrustSensitivityAuthResponse(
                valid=False,
                message=f"令牌无效：{error_msg}（请重新获取令牌）"
            )
        
        payload = jwt_data.get("payload", {})
        department = payload.get("department")
        user_id = payload.get("user_id")
        if not department or not isinstance(department, str):
            logger.warning(f"JWT令牌payload中缺少有效department字段，payload：{payload}")
            deny_count +=1
            #await call_abac_api(False, user_id)
            return TrustSensitivityAuthResponse(
                valid=False,
                message="令牌中未包含有效部门信息（department字段缺失或格式错误）"
            )
        
        type_val = payload.get("data_types")
        if not type_val or not isinstance(type_val, str):
            logger.warning(f"JWT令牌payload中缺少有效type字段，payload：{payload}")
            deny_count +=1
            #await call_abac_api(False, user_id)
            return TrustSensitivityAuthResponse(
                valid=False,
                message="令牌中未包含有效类型信息（type字段缺失或格式错误）"
            )
        
        logger.info(f"JWT验证通过，提取部门信息：{department}，原始类型信息：{type_val}")

        raw_type_list = list(set(type_val.split()))
        raw_type_list = [t.strip() for t in raw_type_list if t.strip()]

        if not raw_type_list:
            logger.warning(f"拆分后的类型列表为空，原始type值：{type_val}")
            deny_count += 1
            #await call_abac_api(False, user_id)
            return TrustSensitivityAuthResponse(
                valid=False,
                message="令牌中type字段格式错误，未提取到有效数据类型"
            )

        data_content_list = []
        for raw_type in raw_type_list:
            data_content = f"{department}{raw_type}"
            data_content_list.append(data_content)

        logger.info(f"生成有效数据内容列表：{data_content_list}")

        sensitivity_standard = """
        个人医疗数据敏感度分级标准（1-5级）：
        1级（公开级）：可公开传播的医疗相关信息或与个人医疗、健康完全无关的内容，无个人隐私关联，无泄露风险，如通用健康科普文章、公开的疾病预防指南、非个人化的医疗常识。
        2级（低敏级）：仅包含个人基础生理指标，单独呈现无隐私风险，泄露后影响极小，如个人血压、体温、心率、身高、体重、日常血糖监测值（未关联确诊疾病）、睡眠时长等。
        3级（中敏级）：常规医疗检查报告或非敏感疾病的诊断记录，涉及个人健康隐私，泄露后造成一定困扰，如普通体检报告（无重大异常）、胃镜/肠镜检查报告、膝盖/胸部X光片报告、血常规/尿常规结果、轻微感冒/肠胃炎的门诊病历。
        4级（高敏级）：慢性疾病或较严重疾病的诊断/治疗数据，泄露后可能影响个人工作、社交或保险权益，如糖尿病/高血压/冠心病的确诊记录及用药方案、甲状腺结节/子宫肌瘤等良性肿瘤的诊断报告、慢性支气管炎的长期治疗病历。
        5级（极高敏级）：重大疾病、心理疾病或涉及隐私性极强的医疗数据，泄露后造成严重心理伤害、社会歧视或重大权益损失，如癌症（肺癌/胃癌等）的病理诊断报告及化疗方案、抑郁症/精神分裂症等心理疾病的诊断记录与治疗档案、艾滋病/梅毒等传染病确诊报告、生殖系统疾病的详细诊疗数据。
        """

        sensitivity_scores = []

        for idx, content in enumerate(data_content_list):
            logger.info(f"第{idx + 1}/{len(data_content_list)}次调用本地大模型进行敏感度评估，输入内容：{content}")

            user_prompt = f"""
        {sensitivity_standard}

        请问“{content}”属于哪一级？请只回答等级数字。
        """

            local_llm_payload = {
                "model": LOCAL_LLM_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "你是一个医疗数据敏感度分级专家系统。"
                            "请严格根据用户给出的分级标准评估用户输入内容的隐私敏感度。"
                            "只输出1到5之间的一个数字，不要输出解释。"
                        )
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 16
            }

            try:
                sens_resp = await client.post(
                    LOCAL_LLM_CHAT_URL,
                    headers={"Content-Type": "application/json"},
                    json=local_llm_payload,
                    timeout=60.0
                )

                sens_resp.raise_for_status()
                sens_data = sens_resp.json()

                model_answer = (
                    sens_data
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )

                logger.info(f"第{idx + 1}次本地大模型原始回答：{model_answer}")

                score = parse_sensitivity_level(model_answer)

                if score is None:
                    logger.warning(f"第{idx + 1}次本地大模型未返回有效1-5等级，内容：{content}")
                    continue

                sensitivity_scores.append(score)
                logger.info(f"第{idx + 1}次调用成功，内容：{content}，敏感度等级：{score}")

            except Exception as e:
                logger.error(f"敏感度模型调用异常：{e}")
                continue

        if not sensitivity_scores:
            logger.error(f"所有敏感度评估均失败，内容：{data_content_list}")
            deny_count += 1
            #await call_abac_api(False, user_id)
            return TrustSensitivityAuthResponse(
                valid=False,
                message="敏感度模型调用失败，未获取到有效分数"
            )

        sensitivity_score = max(sensitivity_scores)
        logger.info(f"最终敏感度等级：{sensitivity_score}")

        try:
            add_value_data = get_configmap(ADD_VALUE_CM)
            addvalue = float(add_value_data.get("addvalue", 0))
            logger.info(f"读取到 addvalue：{addvalue}")
        except Exception as e:
            logger.warning(f"读取addvalue失败，使用默认值0：{e}")
            addvalue = 0
        
        new_saved_trust_score = round(min(1.0, saved_trust_score + addvalue), 3)
        logger.info(f"调整后信任度：{new_saved_trust_score}")

        try:
            match_resp = await client.post(
                MATCH_MODEL_URL,
                params={
                    "trust_score": new_saved_trust_score,
                    "sensitivity_level": sensitivity_score
                },
                timeout=TIMEOUT
            )
            match_resp.raise_for_status()
            match_data = match_resp.json()
            allowed = match_data.get("allowed", False)
            logger.info(f"匹配模型授权结果：{allowed}")
        except httpx.RequestError as e:
            logger.error(f"匹配模型调用失败：{e}")
            deny_count +=1
            #await call_abac_api(False, user_id)
            return TrustSensitivityAuthResponse(
                valid=False,
                message="信任度-敏感度匹配模型不可用"
            )
    
    # 最终结果
    valid = True if allowed else False
    if not valid:
        deny_count +=1

    # ========== 最终只调用一次 ABAC ==========
    #await call_abac_api(valid, user_id)
    # ====================== 修复：缓存本次时间 + 授权结果 ======================
    _REQUEST_CACHE[token] = {
        "time": now,
        "valid": valid
    }

    message = (
        f"授权结果：{'通过' if valid else '拒绝'} | 保存的信任度：{saved_trust_score:.3f} | "
        f"有效数据内容：{data_content_list} | 各内容敏感度分数：{sensitivity_scores} | "
        f"原始信任度：{saved_trust_score} | addvalue：{addvalue} | "
        f"调整后信任度：{new_saved_trust_score}"
    )
    return TrustSensitivityAuthResponse(valid=valid, message=message)

# ------------------------------
# 新增：简易敏感度授权接口
# ------------------------------
@app.post(
    "/auth/sensitivity-simple",
    response_model=TrustSensitivityAuthResponse,
    summary="简易敏感度授权（仅输入敏感度等级）"
)
async def sensitivity_simple_auth(request: SensitivitySimpleAuthRequest):
    """逻辑：仅输入数据敏感度等级→读取addvalue调整信任度→调用匹配模型→返回授权结果"""
    async with httpx.AsyncClient() as client:
        logger.info(f"开始处理简易敏感度授权请求，输入敏感度等级：{request.sensitivity_score}")
        
        # ------------------------------
        # 步骤1：读取addvalue配置并调整信任度
        # ------------------------------
        try:
            # 读取存储addvalue的ConfigMap
            add_value_data = get_configmap(ADD_VALUE_CM)
            addvalue = float(add_value_data.get("addvalue", 0))
            logger.info(f"从ConfigMap[{ADD_VALUE_CM}]读取到addvalue：{addvalue}")
        except Exception as e:
            # 读取失败时使用默认值0（兼容异常场景）
            logger.warning(f"读取addvalue ConfigMap[{ADD_VALUE_CM}]失败，使用默认值0，错误：{e}")
            addvalue = 0
        
        # 调整信任度（限制在0-1范围内）
        new_saved_trust_score = min(1.0, saved_trust_score + addvalue)
        logger.info(f"调整后的信任度分数：{new_saved_trust_score}（原分数：{saved_trust_score}，addvalue：{addvalue}）")

        # ------------------------------
        # 步骤2：调用信任度-敏感度匹配模型
        # ------------------------------
        try:
            match_resp = await client.post(
                MATCH_MODEL_URL,
                params={
                    "trust_score": new_saved_trust_score,  # 调整后的信任度
                    "sensitivity_level": request.sensitivity_score  # 输入的敏感度等级
                },
                timeout=TIMEOUT
            )
            match_resp.raise_for_status()
            match_data = match_resp.json()
            allowed = match_data.get("allowed", False)
            logger.info(f"匹配模型返回授权结果：{'允许' if allowed else '拒绝'}")
        except httpx.RequestError as e:
            # 匹配模型调用失败→ 返回valid: false
            logger.error(f"匹配模型调用失败：{e}")
            return TrustSensitivityAuthResponse(
                valid=False,
                message="信任度-敏感度匹配模型不可用"
            )
    
    # 构建返回结果
    valid = True if allowed else False
    message = (
        f"授权结果：{'通过' if valid else '拒绝'} | 原始信任度：{saved_trust_score:.3f} | "
        f"addvalue：{addvalue} | 调整后信任度：{new_saved_trust_score:.3f} | "
        f"输入敏感度等级：{request.sensitivity_score}"
    )
    return TrustSensitivityAuthResponse(valid=valid, message=message)

@app.post("/evaluate/user-trust", response_model=TrustScoreResponse, summary="用户信任度评估")
async def user_trust_evaluate(request: UserTrustRequest):
    """逻辑：查询ConfigMap补充信息→处理登录时间/分数衰减→调用评估模型→更新保存的信任度→返回打分"""
    # 1. 补充common_device（不变）
    device_data = get_configmap(COMMON_DEVICE_CM)
    common_devices = parse_json_config(COMMON_DEVICE_CM, "common_devices")
    common_device = request.device in common_devices

    # 新增：输出设备标识 + 是否为常用设备
    logger.info(f"设备标识[{request.device}]→是否为常用设备[{common_device}]")
    
    # 2. 补充location（不变）
    ip_location_data = get_configmap(IP_LOCATION_CM)
    location = ip_location_data.get(request.ipaddress, "others")
    if location == "others":
        logger.info(f"IP[{request.ipaddress}]→地理位置[非常用IP]")
    else:
        logger.info(f"IP[{request.ipaddress}]→地理位置[{location} 常用IP]")
    
    # 3. IP→连接方式→access_network_score（不变）
    ip_conn_data = get_configmap(IP_CONNECTION_TYPE_CM)
    connection_type = ip_conn_data.get(request.ipaddress, "unknown")
    access_network_score = CONNECTION_SCORE_MAP.get(connection_type, 0.0)
    logger.info(f"IP[{request.ipaddress}]→连接方式[{connection_type}]→接入得分[{access_network_score}]")
    
    # 4. 修正逻辑：从JSON格式的ConfigMap中获取城市对应的network_risk（不变）
    try:
        # 4.1 读取ConfigMap的JSON字符串（Key=city_risk_map）
        city_risk_json = parse_json_config(CITY_NETWORK_RISK_CM, "city_risk_map")
        # 4.2 根据请求的城市名获取风险值（支持中文）
        network_risk_str = city_risk_json.get(request.city, "0.5")
        # 4.3 转换为浮点数并校验范围
        network_risk = float(network_risk_str)
        if not (0.0 <= network_risk <= 1.0):
            network_risk = 0.5
            logger.warning(f"城市[{request.city}]的网络风险值[{network_risk_str}]超出0-1范围，使用默认值0.5")
    except ValueError:
        # 配置值不是数字时，使用默认0.5
        network_risk = 0.5
        logger.error(f"城市[{request.city}]的网络风险值[{network_risk_str}]格式错误，使用默认值0.5")
    except Exception as e:
        # 其他异常（如JSON解析失败），使用默认0.5
        network_risk = 0.5
        logger.error(f"获取城市[{request.city}]网络风险值失败：{e}，使用默认值0.5")
    logger.info(f"城市[{request.city}]→网络风险值[{network_risk}]")
    
    # ------------------------------
    # 核心新增：处理登录时间和分数衰减逻辑
    # ------------------------------
    global pswdold, bioold, last_pswd_login_time, last_bio_login_time, timegap_pswd, timegap_bio
    current_time = time.time()  # 获取当前时间戳（秒）
    
    # 判断pswd或bio是否为1（浮点精度容错）
    pswd_is_1 = abs(request.pswd - 1.0) < 1e-9
    bio_is_not_0 = abs(request.bio) > 1e-9


    # 处理pswd_is_1的情况
    if pswd_is_1:
        last_pswd_login_time = current_time
        timegap_pswd = 0
        pswdold = request.pswd
        logger.info(
            f"触发密码登录更新：pswd={request.pswd:.4f}(1={pswd_is_1}) → "
            f"last_pswd_login_time={last_pswd_login_time:.2f}，pswdold={pswdold:.4f}，timegap_pswd={timegap_pswd}"
        )
    else:
        # 处理密码登录时间差
        if last_pswd_login_time is None:
            # 首次调用且无密码登录记录 → 初始化
            last_pswd_login_time = current_time
            timegap_pswd = 0
            pswdold = request.pswd
            logger.warning(
                f"首次调用且pswd非1、bio为0 → 初始化密码登录记录：last_pswd_login_time={last_pswd_login_time:.2f}，"
                f"pswdold={pswdold:.4f}，timegap_pswd={timegap_pswd}"
            )
        else:
            # 计算密码登录时间差（秒→分钟）并四舍五入
            time_diff_seconds = current_time - last_pswd_login_time
            time_diff_minutes = time_diff_seconds / 60
            timegap_pswd = round(time_diff_minutes)
            logger.info(
                f"计算密码登录时间差：上次密码登录={last_pswd_login_time:.2f}，当前={current_time:.2f} → "
                f"差值={time_diff_seconds:.2f}秒={time_diff_minutes:.2f}分钟 → 四舍五入timegap_pswd={timegap_pswd}分钟"
            )

    # 处理bio_is_not_0的情况
    if bio_is_not_0:
        last_bio_login_time = current_time
        timegap_bio = 0
        bioold = request.bio  # 修正用户描述中可能的笔误（原描述为pswdold，此处按逻辑调整为bioold）
        logger.info(
            f"触发生物登录更新：bio={request.bio:.4f}(1={bio_is_not_0}) → "
            f"last_bio_login_time={last_bio_login_time:.2f}，bioold={bioold:.4f}，timegap_bio={timegap_bio}"
        )
    else:
        # 处理生物登录时间差
        if last_bio_login_time is None:
            # 首次调用且无生物登录记录 → 初始化
            last_bio_login_time = current_time
            timegap_bio = 0
            bioold = request.bio
            logger.warning(
                f"首次调用且pswd非1、bio为0 → 初始化生物登录记录：last_bio_login_time={last_bio_login_time:.2f}，"
                f"bioold={bioold:.4f}，timegap_bio={timegap_bio}"
            )
        else:
            # 计算生物登录时间差（秒→分钟）并四舍五入
            time_diff_seconds = current_time - last_bio_login_time
            time_diff_minutes = time_diff_seconds / 60
            timegap_bio = round(time_diff_minutes)
            logger.info(
                f"计算生物登录时间差：上次生物登录={last_bio_login_time:.2f}，当前={current_time:.2f} → "
                f"差值={time_diff_seconds:.2f}秒={time_diff_minutes:.2f}分钟 → 四舍五入timegap_bio={timegap_bio}分钟"
            )

    # 读取衰减率配置（新增核心逻辑）
    try:
        decay_rate_data = get_configmap(DECAY_RATE_CM)
        # 读取并转换为浮点数，设置默认值10（兼容配置缺失场景）
        decayrate1 = float(decay_rate_data.get("decayrate1", 10))
        decayrate2 = float(decay_rate_data.get("decayrate2", 10))
        logger.info(f"从ConfigMap[{DECAY_RATE_CM}]读取到衰减率：decayrate1={decayrate1}, decayrate2={decayrate2}")
    except (ValueError, HTTPException) as e:
        # 转换失败或读取失败时使用默认值10
        decayrate1 = 10.0
        decayrate2 = 10.0
        logger.warning(f"读取/解析衰减率配置失败，使用默认值10，错误：{e}")

    # 分别计算密码和生物登录的衰减因子及衰减后的值（修改固定值为动态配置）
    decay_factor_pswd = math.exp(-timegap_pswd / decayrate1)
    decay_factor_bio = math.exp(-timegap_bio / decayrate2)
    decay_pswd = pswdold * decay_factor_pswd * 0.3 if pswdold is not None else 0
    decay_bio = bioold * decay_factor_bio if bioold is not None else 0

    # 确保分数在0-1范围内（防止浮点误差超出范围）
    decay_pswd = max(0.0, min(1.0, decay_pswd))
    decay_bio = max(0.0, min(1.0, decay_bio))

    logger.info(
        f"衰减计算结果：密码衰减因子={decay_factor_pswd:.4f}，衰减后pswd={decay_pswd:.4f}；"
        f"生物衰减因子={decay_factor_bio:.4f}，衰减后bio={decay_bio:.4f}"
    )
    
    real_hour = (request.time + 8) % 24
    logger.info(
        f"时间={real_hour}"
    )
    # ------------------------------
    # 调用模型（使用衰减后的pswd和bio）
    # ------------------------------
    model_request = {
        "subject_type": "user",
        "common_device": common_device,
        "time": real_hour,
        "location": location,
        "bio": decay_bio,  # 使用衰减后的bio
        "pswd": decay_pswd,  # 使用衰减后的pswd
        "access_network_score": access_network_score,
        "network_risk": network_risk
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                USER_TRUST_MODEL_URL,
                json=model_request,
                timeout=TIMEOUT
            )
            resp.raise_for_status()
            result = resp.json()
            
            # ------------------------------
            # 核心修改：读取trust_score_add_value并计算最终信任度
            # ------------------------------
            try:
                # 读取信任度加分值配置
                trust_add_data = get_configmap(TRUST_SCORE_ADD_CM)
                trust_score_add_value = float(trust_add_data.get("trust_score_add_value", 0.0))
                logger.info(f"从ConfigMap[{TRUST_SCORE_ADD_CM}]读取到trust_score_add_value：{trust_score_add_value}")
            except (ValueError, HTTPException) as e:
                # 读取/转换失败时使用默认值0.0
                trust_score_add_value = 0.0
                logger.warning(f"读取/解析trust_score_add_value失败，使用默认值0.0，错误：{e}")
            
            # 计算最终信任度（确保在0-1范围内）
            original_trust_score = result["trust_score"]
            final_trust_score = original_trust_score + trust_score_add_value
            final_trust_score = max(0.0, min(1.0, final_trust_score))  # 限制范围在0-1
            
            # 更新全局保存的信任度（使用最终值）
            global saved_trust_score
            saved_trust_score = final_trust_score
            
            logger.info(
                f"信任度评估成功：模型返回值={original_trust_score:.3f} + 加分值={trust_score_add_value:.3f} = 最终值={final_trust_score:.3f}，"
                f"已更新保存的信任度为：{saved_trust_score:.3f}"
            )
            final_trust_score = float(f"{final_trust_score:.2f}")
            return TrustScoreResponse(
                trust_score=final_trust_score,  # 返回加完分后的信任度
                status=result["status"],
                message=f"{result['message']} | 模型原始信任度：{original_trust_score:.3f} | 加分值：{trust_score_add_value:.3f} | 最终信任度：{final_trust_score:.3f}"
            )
        except httpx.RequestError as e:
            logger.error(f"信任度评估模型调用失败：{e}")
            raise HTTPException(status_code=503, detail="用户信任度评估模型不可用")

# ------------------------------
# 新增：mac/imsi白名单校验接口（核心新增，对应用户需求）
# ------------------------------
@app.post(
    "/auth/5g",  # 与用户示例curl的接口路径保持一致
    response_model=AuthResponse,
    summary="MAC/IMSI白名单授权校验"
)
async def mac_imsi_auth(request: MacImsiAuthRequest):
    """
    逻辑：校验MAC地址是否在MAC白名单ConfigMap中，且IMSI号码是否在IMSI白名单ConfigMap中
    仅当两者均存在时，返回授权通过；任一不存在或配置读取失败，返回授权拒绝
    """
    # 新增：声明全局拒绝计数变量
    global deny_count
    logger.info(f"开始处理IMSI授权请求：IMSI={request.imsi}") #MAC/    MAC={request.mac}，
    
    # 步骤1：统一MAC地址格式（转大写，避免大小写匹配问题）
    target_mac = request.mac.upper()
    target_imsi = request.imsi.strip()
    
    # 步骤2：读取MAC白名单和IMSI白名单
    try:
        mac_whitelist = get_whitelist_from_cm(MAC_WHITELIST_CM)
        imsi_whitelist = get_whitelist_from_cm(IMSI_WHITELIST_CM)
    except HTTPException as e:
        logger.error(f"读取白名单ConfigMap失败：{e.detail}")
        # # 新增：配置读取失败 → 拒绝计数+1
        # deny_count += 1
        return AuthResponse(
            result="deny",
            message=f"授权失败：配置读取异常（{e.detail}）"
        )
    
    # 步骤3：执行匹配判断
    mac_is_valid = target_mac in mac_whitelist
    imsi_is_valid = target_imsi in imsi_whitelist
    
    # 步骤4：构建返回结果
    if mac_is_valid and imsi_is_valid:
        logger.info(f"授权通过：IMSI={target_imsi}在白名单中") #MAC={target_mac}、
        return AuthResponse(
            result="allow",
            message=f"授权通过：IMSI={target_imsi}为合法资源" #MAC={target_mac}、
        )
    else:
        error_details = []
        # if not mac_is_valid:
        #     error_details.append(f"MAC={target_mac}不在白名单中")
        if not imsi_is_valid:
            error_details.append(f"IMSI={target_imsi}不在白名单中")
        error_msg = "授权拒绝：" + "；".join(error_details)
        logger.warning(error_msg)
        # # 新增：校验不通过 → 拒绝计数+1
        # deny_count += 1
        return AuthResponse(
            result="deny",
            message=error_msg
        )

# ====================== 仅新增：获取授权拒绝次数接口 ======================
@app.get("/auth/abac", summary="获取授权拒绝总次数")
async def get_deny_count():
    return {"deny_totalabac_count": deny_count}
# ====================================================================

# ====================== 仅新增：获取授权拒绝次数接口 ======================
@app.get("/auth/rbac", summary="获取授权拒绝总次数")
async def get_deny_count2():
    return {"deny_totalrbac_count": deny_count2}
# ====================================================================

# 健康检查接口（K8s探针使用）
@app.get("/health", summary="健康检查")
async def health_check():
    return {
        "status": "healthy",
        "current_trust_score": saved_trust_score,
        "last_bio_login_time": last_bio_login_time,
        "last_pswd_login_time": last_pswd_login_time,
        "pswdold": pswdold,
        "bioold": bioold
    }
