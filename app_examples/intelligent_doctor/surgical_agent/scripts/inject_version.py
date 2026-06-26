# Copyright (c) 2026 PCL-CCNN
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <version> <git_commit> <build_time>")
        sys.exit(1)

    version = sys.argv[1]
    git_commit = sys.argv[2]
    build_date = sys.argv[3]  

    try:
        parts = version.split('.')
        if len(parts) >= 3:
            major = parts[0]
            minor = parts[1]
            patch = parts[2]
        elif len(parts) == 2:
            major = parts[0]
            minor = parts[1]
            patch = "0"
        elif len(parts) == 1:
            major = parts[0]
            minor = "0"
            patch = "0"
        else:
            major = "0"
            minor = "0"
            patch = "0"
    except:
        major = "0"
        minor = "0"
        patch = "0"

    output_dir = "src"
    output_file = os.path.join(output_dir, "version.py")

    os.makedirs(output_dir, exist_ok=True)

    content = f'''# Copyright (c) 2026 PCL-CCNN
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# -*- coding: utf-8 -*-

__version__ = "{version}"
__major__ = {major}
__minor__ = {minor}
__patch__ = {patch}
__git_commit__ = "{git_commit}"
__build_time__ = "{build_date}"  


def get_version() -> str:
    return __version__


def get_version_info() -> dict:
    return {{
        "version": __version__,
        "major": __major__,
        "minor": __minor__,
        "patch": __patch__,
        "build_time": __build_time__,
        "git_commit": __git_commit__,
    }}
'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"version info injected into {output_file}")

if __name__ == "__main__":
    main()