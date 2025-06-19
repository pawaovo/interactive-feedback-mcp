# ![Interactive Feedback MCP](./1a7ef-zmno1-001.png) Interactive Feedback MCP

一个功能完整的 [MCP Server](https://modelcontextprotocol.io/)，用于在AI辅助开发工具（如 [Cursor](https://www.cursor.com)、[Cline](https://cline.bot) 、 [Windsurf](https://windsurf.com)）和[Augment]插件中实现人机协作工作流。该服务器提供图形化交互界面、多媒体处理、对话历史记录、文本优化等丰富功能，让AI与您之间更好地协作。

**详细信息请参阅：**
*   [功能说明.md](./功能说明.md) - 了解本服务提供的各项功能。
*   [安装与配置指南.md](./安装与配置指南.md) - 获取详细的安装和设置步骤。

**注意：** 此服务器设计为与MCP客户端（例如Cursor、VS Code）在本地一同运行，因为它需要直接访问用户的操作系统以显示UI和执行键盘/鼠标操作。

## 🖼️ 示例

![Interactive Feedback Example](https://i.postimg.cc/pL99L9h5/Q1.png)
![Interactive Feedback Example](https://i.postimg.cc/Nf8t7B3C/Q2.png)
![Interactive Feedback Example](https://i.postimg.cc/gJ6FwWyD/Q3.png)
![Interactive Feedback Example](https://i.postimg.cc/pXR4v8Sk/Q4.png)
*(请注意，示例图片可能未反映最新的UI调整，但核心交互流程保持不变)*

## 💡 为何使用此工具？

1.在像Cursor这样的环境中，您发送给LLM的每个提示都被视为一个独立的请求——每个请求都会计入您的每月限额（例如，500个高级请求）。当您迭代模糊指令或纠正被误解的输出时，这会变得效率低下，因为每次后续澄清都会触发一个全新的请求。

此MCP服务器引入了一种变通方法：它允许模型在最终确定响应之前暂停并请求澄清。模型不会直接完成请求，而是触发一个工具调用 (`interactive_feedback`)，打开一个交互式反馈窗口。然后，您可以提供更多细节或要求更改——模型会继续会话，所有这些都在单个请求内完成。

从本质上讲，这只是巧妙地利用工具调用来推迟请求的完成。由于工具调用不计为单独的高级交互，因此您可以在不消耗额外请求的情况下循环执行多个反馈周期。

简而言明，这有助于您的AI助手在猜测之前请求澄清，而不会浪费另一个请求。这意味着更少的错误答案、更好的性能和更少的API使用浪费。

2.一定程度上可替代原有的IDA对话栏，直接使用MCP服务与AI对话

- **💰 减少高级API调用：** 避免浪费昂贵的API调用来基于猜测生成代码。
- **✅ 更少错误：** 行动前的澄清意味着更少的错误代码和时间浪费。
- **⏱️ 更快周期：** 快速确认胜过调试错误的猜测。
- **🎮 更好协作：** 将单向指令转变为对话，让您保持控制。

## 🌟 核心功能与使用技巧

### 处理图片
- **粘贴：** 在反馈窗口的文本输入框中按 `Ctrl+V` (或 `Cmd+V`) 粘贴图片。您可以同时粘贴多张图片和文本。
- **拖拽：** 直接从文件管理器拖拽图片文件到文本输入框中。
- **选择：** 点击"选择文件"按钮，通过文件对话框选择图片文件。
- **图片预览：** 添加的图片会在输入框下方显示可点击的缩略图预览。点击缩略图可以移除对应的图片。

### 文件引用
- **拖拽文件：** 将任意文件从文件管理器拖拽到文本输入框，会生成蓝色的文件引用（如 `@文件名.txt`）。
- **选择文件：** 点击"选择文件"按钮选择多个文件，支持图片和普通文件的混合选择。
- **智能处理：** 系统自动识别图片文件和普通文件，分别进行相应的处理和显示。

### 常用语
- **hover预览：** 鼠标悬停在"常用语"按钮上可快速预览所有常用语，支持滚动查看。
- **快速插入：** 在预览窗口中点击常用语可直接插入到输入框，无需打开管理对话框。
- **管理：** 点击"常用语"按钮打开管理对话框，可以添加、编辑、删除和排序常用语。

### 原生终端操作
- **hover预览：** 鼠标悬停在"终端"按钮上可预览可用的终端类型（PowerShell、Git Bash、Command Prompt）。
- **快速启动：** 在预览窗口中点击终端类型可直接打开对应的原生终端窗口。
- **直接输入：** 在终端输出区域内直接输入命令，完全模拟真实终端体验。
- **智能交互：** 支持命令历史浏览、键盘导航、彩色输出等完整终端功能。
- **工作目录：** 终端会自动设置项目根目录为工作目录，方便进行项目相关操作。

### 文本优化和增强
- **一键优化：** 点击"优化"按钮将口语化输入转换为结构化指令，提高AI理解准确性。
- **自定义增强：** 点击"增强"按钮，可使用自定义提示词对文本进行特定处理。
- **API配置：** 在设置页面配置OpenAI、Gemini、DeepSeek等AI提供商的API密钥。
- **撤销功能：** 优化后可使用Ctrl+Z撤销，恢复原始文本内容。

### 窗口截图
- **矩形截图：** 点击截图按钮后，UI窗口自动最小化，可进行矩形区域选择截图。
- **自动集成：** 截图完成后自动添加到输入内容中，与图片功能无缝集成。
- **实时预览：** 截图选择过程中提供实时的选择区域预览效果。

### 界面布局
- **布局切换：** 在设置页面可以选择垂直布局（上下分布）或水平布局（左右分布）。
- **分割器拖拽：** 拖拽分割器手柄可以调整各区域的大小，双击分割器可重置为默认比例。
- **状态保存：** 布局选择和分割器位置会自动保存，下次启动时恢复。

### 对话历史记录
- **自动记录：** 系统自动记录所有AI助手与用户的对话历史，按会话智能分组。
- **历史查看：** 点击主界面的历史记录按钮打开对话历史窗口，查看所有历史会话。
- **搜索过滤：** 在历史记录窗口顶部搜索框中输入关键词，实时过滤相关对话。
- **详情展开：** 点击会话卡片可展开查看完整的对话内容，包括AI回复和用户反馈。
- **窗口管理：** 历史记录窗口支持自由调整大小，系统会记住窗口尺寸，下次打开时自动恢复。
- **清除操作：** 左下角"清除全部"按钮可一键删除所有历史记录，操作前会弹出确认对话框。
- **智能限制：** 系统自动维护最多50组会话记录，超出时自动删除最旧的记录。

### 显示模式配置
- **简单模式：** 显示AI处理后的简洁问题，适合快速交互。
- **完整模式：** 显示AI的原始完整回复内容，适合详细查看。
- **动态切换：** 可在设置页面实时切换显示模式，立即生效。

## 🛠️ 工具

此服务器通过模型上下文协议 (MCP) 公开以下工具：

### `interactive_feedback`
- **功能：** 向用户发起交互式会话，显示提示信息，提供可选选项，并收集用户的文本、图片和文件引用反馈。支持多种交互方式包括文本输入、图片粘贴/拖拽、文件拖拽/选择等。
- **参数：**
    - `message` (str, 可选): 简单模式下显示的简洁问题或提示
    - `full_response` (str, 可选): 完整模式下显示的AI原始完整回复内容
    - `predefined_options` (List[str], 可选): 一个字符串列表，每个字符串代表一个用户可以选择的预定义选项。如果提供，这些选项会显示为复选框。
- **智能回退机制：**
    - **简单模式**：优先使用 `message` 参数，如果为空则自动回退到 `full_response`
    - **完整模式**：优先使用 `full_response` 参数，如果为空则自动回退到 `message`
    - **实时模式检测**：每次调用都读取最新的用户模式配置，支持动态切换
    - **错误处理**：只有当两个参数都为空时才返回错误，避免不必要的调用失败
- **用户交互方式：**
    - **文本输入**：在主输入框中输入反馈文本
    - **图片处理**：通过Ctrl+V粘贴或拖拽图片文件
    - **文件引用**：通过拖拽文件或点击"选择文件"按钮添加文件引用
    - **常用语**：通过hover预览或管理对话框快速插入预设短语
    - **终端操作**：通过终端按钮打开嵌入式终端窗口
    - **布局调整**：通过拖拽分割器调整界面布局
    - **文本优化**：通过优化和增强按钮处理输入文本
    - **窗口截图**：通过截图按钮进行矩形选择截图
    - **对话历史**：查看历史对话记录、搜索过滤、清除管理
- **返回给AI助手的数据格式：**
  该工具会返回一个包含结构化反馈内容的元组 (Tuple)。元组中的每个元素可以是字符串 (文本反馈或文件引用信息) 或 `fastmcp.Image` 对象 (图片反馈)。
  具体来说，从UI收集到的数据会转换成以下 `content` 项列表，并由 `server.py` 进一步处理成 FastMCP兼容的元组：
  ```json
  // UI返回给server.py的原始JSON结构示例
  {
    "content": [
      {"type": "text", "text": "用户的文本反馈..."},
      {"type": "image", "data": "base64_encoded_image_data", "mimeType": "image/jpeg"},
      {"type": "file_reference", "display_name": "@example.txt", "path": "/path/to/local/example.txt"}
      // ... 可能有更多项
    ]
  }
  ```
  *   **文本内容** (`type: "text"`)：包含用户输入的文本和/或选中的预定义选项组合文本。
  *   **图片内容** (`type: "image"`)：包含 Base64 编码后的图片数据和图片的 MIME 类型 (如 `image/jpeg`)。这些在 `server.py` 中会被转换为 `fastmcp.Image` 对象。
  *   **文件引用** (`type: "file_reference"`)：包含用户拖拽或选择的文件的显示名 (如 `@filename.txt`) 和其在用户本地的完整路径。这些信息通常会作为文本字符串传递给AI助手。

  **注意：**
  * 即便没有任何用户输入（例如用户直接关闭反馈窗口），工具也会返回一个表示"无反馈"的特定消息，如 `("[User provided no feedback]",)`。

### `optimize_user_input`
- **功能：** 使用配置的LLM API来优化或增强用户输入的文本，将口语化、可能存在歧义的输入转化为更结构化、更清晰、更便于AI模型理解的文本。
- **参数：**
    - `original_text` (str): **必须参数**。用户的原始输入文本
    - `mode` (str): **必须参数**。优化模式：
        - `'optimize'`: 一键优化，使用预设的通用优化指令
        - `'reinforce'`: 提示词强化，使用用户自定义的强化指令
    - `reinforcement_prompt` (str, 可选): 在 'reinforce' 模式下用户的自定义指令
- **支持的AI提供商：**
    - **OpenAI**: GPT-4o-mini 等模型
    - **Google Gemini**: Gemini-2.0-flash 等模型
    - **DeepSeek**: DeepSeek-chat 等模型
    - **火山引擎**: DeepSeek-v3 等模型
- **返回：** 优化后的文本内容或错误信息

## 📦 安装

### 方式一：直接从PyPI安装（推荐）

**使用uvx（推荐）：**
```bash
# 直接运行，无需安装
uvx interactive-feedback@latest
```

**使用pip：**
```bash
pip install interactive-feedback
```

### 方式二：开发安装

1.  **先决条件：**
    *   Python 3.11 或更新版本。
    *   [uv](https://github.com/astral-sh/uv) (一个快速的Python包安装和解析工具)。按以下方式安装：
        *   Windows: `pip install uv`
        *   Linux/macOS: `curl -LsSf https://astral.sh/uv/install.sh | sh`
        *   或者参考 `uv` 官方文档获取其他安装方式。

2.  **获取代码：**
    *   克隆此仓库：
        `git clone https://github.com/pawaovo/interactive-feedback-mcp.git`
    *   或者下载源代码压缩包并解压。

3.  **安装依赖：**
    *   进入仓库目录 (`cd interactive-feedback-mcp`)。
    *   **推荐方式（现代）：**
        ```bash
        # 使用 uv（推荐）
        uv pip install -e .

        # 或使用 pip
        pip install -e .
        ```
    *   **兼容方式：**
        ```bash
        # 使用 requirements.txt
        uv pip install -r requirements.txt

        # 如果需要开发工具
        uv pip install -r requirements-dev.txt
        ```
    *   **说明：** 所有必要的依赖（包括 `pyperclip`, `Pillow`, `pywin32` 等）都已在 `pyproject.toml` 和 `requirements.txt` 中定义，会自动安装。

## ⚙️ 配置

### 方式一：使用uvx（推荐）

将以下配置添加到您的 `claude_desktop_config.json` (Claude Desktop) 或 `mcp_servers.json` (Cursor, 通常在 `.cursor-ai/mcp_servers.json` 或用户配置目录中)：

```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "uvx",
      "args": [
        "interactive-feedback@latest"
      ],
      "timeout": 600,
      "autoApprove": [
        "interactive_feedback"
      ]
    }
  }
}
```

### 推荐配置方式：uvx + UI 设置

**MCP JSON 中仅配置服务，API key 通过 UI 设置页面管理：**

```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "uvx",
      "args": [
        "interactive-feedback@latest"
      ],
      "timeout": 600,
      "autoApprove": [
        "interactive_feedback"
      ]
    }
  }
}
```

**优势：**
- ✅ **零安装**：无需手动安装任何依赖
- ✅ **自动更新**：总是使用最新版本
- ✅ **灵活配置**：API key 通过 UI 界面管理
- ✅ **多提供商**：支持多个 AI 提供商配置和切换
- ✅ **用户友好**：直观的图形界面配置

**使用步骤：**
1. 在 MCP JSON 中添加上述配置
2. 重启 AI 助手
3. 在 UI 设置页面中配置 API key
4. 开始使用所有功能

### 方式二：使用pip安装后配置

如果您使用pip安装，配置如下：

```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "interactive-feedback",
      "timeout": 600,
      "autoApprove": [
        "interactive_feedback"
      ]
    }
  }
}
```

### 方式三：开发模式配置

如果您克隆了仓库进行开发，配置如下：

**重要提示：** 将 `/path/to/interactive-feedback-mcp` 替换为您在系统上克隆或解压本仓库的 **实际绝对路径**。
```json
{
  "mcpServers": {
    "interactive-feedback": {
      "command": "uv",
      "args": [
        "--directory",
        "path/to/interactive-feedback-mcp",
        "run",
        "server.py"
      ],
      "timeout": 600,
      "autoApprove": [
        "interactive_feedback"
      ]
    }
  }
}
```

**关于 `command` 和 `args` 的说明:**
- 如果 `uv` 在您的系统路径中，并且您希望 `uv` 管理虚拟环境和运行脚本，可以使用 `"command": "uv", "args": ["run", "python", "server.py"]`。
- 如果您更倾向于直接使用系统Python（并已在全局或项目虚拟环境中安装了依赖），可以使用 `"command": "python", "args": ["server.py"]` (或python3)。
- **`cwd` (Current Working Directory):** 强烈建议设置 `cwd` 为此项目的根目录，以确保脚本能正确找到其依赖文件。

2.  将以下自定义规则添加到您的AI助手中 (例如，在 Cursor 的设置 -> Rules -> User Rules):

    ```text
    Always respond in Chinese-simplified
    你是 IDE 的 AI 编程助手，遵循核心工作流（研究 -> 构思 -> 计划 -> 执行 -> 优化 -> 评审）用中文协助用户，面向专业程序员，交互应简洁专业，避免不必要解释。

    [沟通守则]
    1.  响应以模式标签 `[模式：X]` 开始，初始为 `[模式：研究]`。
    2.  核心工作流严格按 `研究 -> 构思 -> 计划 -> 执行 -> 优化 -> 评审` 顺序流转，用户可指令跳转。

    [核心工作流详解]
    1.  `[模式：研究]`：理解需求。
    2.  `[模式：构思]`：提供至少两种可行方案及评估（例如：`方案 1：描述`）。
    3.  `[模式：计划]`：将选定方案细化为详尽、有序、可执行的步骤清单（含原子操作：文件、函数 / 类、逻辑概要；预期结果；新库用 `Context7` 查询）。不写完整代码。完成后用 `interactive-feedback` 请求用户批准。
    4.  `[模式：执行]`：必须用户批准方可执行。严格按计划编码执行。计划简要（含上下文和计划）存入 `./issues/ 任务名.md`。关键步骤后及完成时用 `interactive-feedback` 反馈。
    5.  `[模式：优化]`：在`[模式：执行]完成后，必须自动进行本模式[模式：优化]，自动检查并分析本次任务已实现（仅本次对话产生的相关代码），在[模式：执行]下产生的相关代码。聚焦冗余、低效、垃圾代码，提出具体优化建议（含优化理由与预期收益），用户确认后执行相关优化功能。
    6.  `[模式：评审]`：对照计划评估执行结果，报告问题与建议。完成后用 `mcp-feedback-enhanced` 请求用户确认。

    [快速模式]
    `[模式：快速]`：跳过核心工作流，快速响应。完成后用 `interactive-feedback` 请求用户确认。

    [主动反馈与 MCP 服务]
    # MCP interactive-feedback 规则
    1. 在任何流程、任务、对话进行时，无论是询问、回复、或完成阶段性任务，皆必须调用 MCP interactive-feedback。
    2. 每当收到用户反馈，若反馈内容非空，必须再次调用 MCP interactive-feedback，并根据反馈内容调整行为。
    3. 仅当用户明确表示「结束」或「不再需要交互」时，才可停止调用 MCP interactive-feedback，流程才算结束。
    4. 除非收到结束指令，否则所有步骤都必须重复调用 MCP interactive-feedback。
    5. 完成任务前，必须使用 MCP interactive-feedback 工具向用户询问反馈。
    * **MCP 服务 **：
        * `interactive-feedback`: 用户反馈。
        * `Context7`: 查询最新库文档 / 示例。
        * `DeepWiki`: 查询相关 GitHub 仓库的文档 / 示例。
        * 优先使用 MCP 服务。
    ```

    这将确保您的AI助手遵循专业的编程工作流，并在适当时机使用此MCP服务器进行交互式反馈。

## 🔧 故障排除

如果在安装或配置过程中遇到问题，请参考以下解决方案：

### uvx环境问题

**问题**：MCP配置中使用 `"command": "uvx"` 时出现"命令未找到"错误。

**解决方案**：

1. **检查uvx安装位置**：
   ```bash
   # Windows
   where uvx

   # Linux/macOS
   which uvx
   ```

2. **使用完整路径**：

   将MCP配置中的 `"uvx"` 替换为完整路径，例如：
   ```json
   {
     "mcpServers": {
       "interactive-feedback": {
         "command": "D:/python/Scripts/uv.exe",
         "args": ["tool", "run", "interactive-feedback@latest"],
         "timeout": 600,
         "autoApprove": ["interactive_feedback"]
       }
     }
   }
   ```

### MCP配置问题

**问题**：AI助手无法识别或启动服务。

**解决方案**：

1. **验证JSON格式**：确保配置文件语法正确
2. **检查文件位置**：确认 `mcp_servers.json` 在正确目录
3. **重启AI助手**：修改配置后重启应用程序
4. **询问AI助手**：将配置文件内容提供给AI，请求配置建议

**示例**：在Cursor中询问："我在配置MCP服务时遇到问题，请帮我检查这个配置：[粘贴您的配置]"

详细的故障排除指南请参阅 [安装与配置指南.md](./安装与配置指南.md#故障排除)。

## English Notes

- If you encounter encoding issues, you may need to add the following to the "interactive-feedback" section of `mcp.json`:
  ```json
  "env": {
    "PYTHONIOENCODING": "utf-8"
  }
  ```
- This ensures proper UTF-8 encoding for Python processes started by the MCP server.

## 🙏 致谢

- 原始概念和初步开发由 Fábio Ferreira ([@fabiomlferreira](https://x.com/fabiomlferreira)) 完成。
- 由 pawa ([@pawaovo](https://github.com/pawaovo)) 进行了功能增强，并借鉴了 [interactive-feedback-mcp](https://github.com/noopstudios/interactive-feedback-mcp) 项目中的一些想法。
- 当前版本由 pawaovo 维护和进一步开发。

## 📄 许可证

此项目使用 MIT 许可证。详情请参阅 `LICENSE` 文件。


