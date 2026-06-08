# Cybertwin Based Cloud Native Network

The **CCNN (Cybertwin-based Cloud Native Network)** project constructs and verifies a cloud-native network architecture based on network digital twins. Taking distributed collaborative inference powered by network digital twins as an example, it validates the application-centric networking design philosophy of cloud-native networks. Meanwhile, it demonstrates the cornerstone for the implementation of cloud-native networks: fundamental services of cybertwin and the AI Twin personal assistant.

## Core Features
1. **Personal Agent Service**: Provides real-time intelligent dialogue services and enables real-time communication via WebSocket to ensure low-latency interaction between users and agents.
2. **Cybertwin Security Proxy**: As the core security module of the system, it implements a zero-trust security mechanism.
3. **Cybertwin Data Proxy**: Provides personal data management services. 
4. **Cybertwin Communication Proxy**: Under a unified security authentication system, it provides users with a one-hop, seamless cloud access experience across Wi-Fi, 5G and the Internet. It offers a secure, reliable, high-speed and smooth channel for users to access personal intelligent Agent applications and third-party applications.
5. **Distributed Medical Collaborative Reasoning Based on AI Twin**: Enables users to access AI Twin applications via 5G access networks deployed in edge data centers, demonstrating the capabilities of the network twin access proxy and the computing-network converged cloud-native network architecture featuring cloud-based networking and one-hop cloud access.

## Project Structure 
``` 
CCNN
├── End User【Mobile phones, computers】
├── Access Network
│    └── access
│          ├── 5G                                # 5G Core Network
│          └── wifi                              # wifi access network
├── Frontend
├── AI Twin
│    ├── Cybertwin
│    │     ├── Security Proxy                   # network digital twin security proxy
│    │     │     ├── auth-service               # authorization service module: Responsible for permission management. 
│    │     │     ├── datamodel-service          # data sensitivity classification model inference service module 
│    │     │     ├── matchmodel-service         # matching model inference service module
│    │     │     └── usermodel-service	         # user trust vvaluation module: responsible for user attribute management and trust value calculation.
│    │     ├── Data Proxy                       # network digital twin data proxy server
│    │     ├── Communication Proxy              # network digital communication proxy server
│    │     └── Resource Collaboration 【planed】
│    └── Agent                                  # personal agent service of network digital twin 
├── APP Examples
│    └── intelligent-doctor                     # intelligent doctor is a sample scenario used to interact with AI Twin 
│          ├── triage-doctor-agent              # triage doctor agent receives medical inquiries, triggers diagnoses from various specialist doctors, and summarizes the diagnostic results.
│          ├── surgical-agent                   # surgeon doctor agent receives and diagnoses surgery issues from the triage doctor, and requests personal data access from the data proxy as required by the diagnosis.
│          ├── internal-agent                   # internal doctor agent receives and diagnoses internal issues from the triage doctors, and requests personal from data proxy as requirements by the diagnosis.
│          └── medical-materials-service        # medical meterials service which manages personal medical data such as user profiles and medical treatment records.
└── Demo
```

### Core Components
#### Access Network/5G
**Access Network/5G** is an implementation of the 3GPP specifications for the 5G Core Network. Under a unified cybertwin security authentication system, it provides users with a one-hop, seamless cloud access experience across 5G. At the moment, it contains the following network elements:
* Access and Mobility Management Function (**AMF**)
* Authentication Server Management Function (**AUSF**)
* Network Repository Function (**NRF**)
* Session Management Function (**SMF**)
* Unified Data Management (**UDM**)
* Unified Data Repository (**UDR**)
* User Plane Function (**UPF**)

#### Security Proxy

As the core security module of the system, **Security Proxy** implements a zero-trust security mechanism. This module integrates user trust evaluation, data sensitivity classification, and a trust-sensitivity matching model to support dynamic authorization decisions and ensure the security of data resources. It provides OIDC-based authentication and authorization services for unified user identity authentication and permission management. It supports user management functions including registration, login, and profile management. Furthermore, it incorporates face recognition technology to deliver multi-factor authentication capabilities.

#### Data Proxy

**Data Proxy** provides personal data management services. It offers data query services based on the MCP protocol, supporting multi-dimensional personal data retrieval by user ID, department and other attributes. JWT authentication is integrated to ensure secure data access.

#### AI Twin/Agent

**AI Twin/Agent** provides real-time intelligent dialogue services and enables real-time communication via WebSocket to ensure low-latency interaction between users and agents. It integrates the A2A protocol for inter-agent communication, supporting cross-system data requests and task collaboration. Additionally, it supports the MCP protocol to enable the invocation and management of AI tools.

#### Intelligent Doctor

**Intelligent Doctor** is a sample scenario of CCNN. When a user sends a query to the AI Twin through the front-end interface, the AI Twin accesses the smart healthcare application based on the user’s needs. The smart healthcare system then inquires the network twin — the foundational service of AI Twin — about the data location for diagnosis and the corresponding data access permissions, demonstrating the capabilities of the network twin’s intelligent assistant, data proxy, and security proxy.

The smart healthcare triage Agent accesses specialist Agents and data in different regions based on data locations and consultation requirements, and proposes further diagnostic inquiries, verifying the unified scheduling capability of communication, computing, and storage resources.

In response to these further consultation needs, additional diagnostic data is requested from the cybertwin. The AI Twin then invokes the smart bracelet application to collect more data and provides it to the smart healthcare system, which finally returns diagnosis results and recommendations. This process realizes the application-centric networking of the cloud-native network and its ability to uniformly schedule and orchestrate communication, computing, and storage resources.

## Quick Install
Use the following command to build Docker images for all services:
```bash
git clone https://github.com/ccnn-pcl/ccnn.git
cd ccnn
make all 
```

## Deployment

## Run Example

## License
Apache License, Version 2.0 ([LICENSE](./LICENSE))
