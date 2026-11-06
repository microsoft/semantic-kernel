# 语义内核 (Semantic Kernel)

<p align="center">
  <a href="README.md">English</a> · <b>简体中文</b>
</p>

> [!IMPORTANT]
> Semantic Kernel 现已升级演进为 [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)！Microsoft Agent Framework (MAF) 是 Semantic Kernel 面向企业级生产场景的官方继承者。Microsoft Agent Framework 现已正式发布 1.0 生产就绪版本：提供高度稳定的 API 与长效支持承诺。无论你是构建单一专属 AI 助手，还是编排由专业化智能体组成的大规模集群，Microsoft Agent Framework 1.0 都能为你提供企业级多智能体协同编排、多模型供应商接入，以及基于 A2A 与 MCP 协议的跨运行时互操作能力。
>
> 欢迎阅读相关博客与文档：[Agent Framework 官方博客：Semantic Kernel 与 Microsoft Agent Framework](https://devblogs.microsoft.com/agent-framework/semantic-kernel-and-microsoft-agent-framework/)，并参考 [Semantic Kernel 迁移指南](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-semantic-kernel)。

**基于这套企业级编排框架，构建强大的 AI 智能体与多智能体协同系统**

[![License: MIT](https://img.shields.io/github/license/microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/blob/main/LICENSE)
[![Python package](https://img.shields.io/pypi/v/semantic-kernel)](https://pypi.org/project/semantic-kernel/)
[![Nuget package](https://img.shields.io/nuget/vpre/Microsoft.SemanticKernel)](https://www.nuget.org/packages/Microsoft.SemanticKernel/)
[![Discord](https://img.shields.io/discord/1063152441819942922?label=Discord&logo=discord&logoColor=white&color=d82679)](https://aka.ms/SKDiscord)

## 什么是 Semantic Kernel？

Semantic Kernel 是一套与模型解耦的开源 SDK，赋能开发者构建、编排并部署各类 AI 智能体（AI Agents）与多智能体系统（Multi-Agent Systems）。无论你是搭建轻量级对话助理，还是设计高度复杂的分布式多智能体业务流水线，Semantic Kernel 都能以企业级的可靠性与灵活性为你提供完备的工具支撑。

## 系统环境要求 (System Requirements)

- **Python**: 3.10 及以上
- **.NET**: .NET 10.0 及以上
- **Java**: JDK 17 及以上
- **支持操作系统**: Windows、macOS、Linux

## 核心特性 (Key Features)

- **多模型灵活适配（Model Flexibility）**：无缝连接任意大语言模型，原生支持 [OpenAI](https://platform.openai.com/docs/introduction)、[Azure OpenAI](https://azure.microsoft.com/en-us/products/ai-services/openai-service)、[Hugging Face](https://huggingface.co/)、[NVIDIA](https://www.nvidia.com/en-us/ai-data-science/products/nim-microservices/) 等主流平台。
- **智能体框架（Agent Framework）**：构建具备工具/插件（Tools/Plugins）调用能力、上下文记忆（Memory）与任务规划（Planning）能力的模块化 AI Agent。
- **多智能体系统（Multi-Agent Systems）**：编排由多专长智能体协同合作的复杂端到端工作流。
- **插件生态体系（Plugin Ecosystem）**：支持使用原生代码函数、提示词模板、OpenAPI 规范或模型上下文协议（Model Context Protocol, MCP）无限扩展系统能力。
- **向量数据库集成（Vector DB Support）**：无缝集成 [Azure AI Search](https://learn.microsoft.com/en-us/azure/search/search-what-is-azure-search)、[Elasticsearch](https://www.elastic.co/)、[Chroma](https://docs.trychroma.com/docs/overview/getting-started) 等主流向量检索引擎。
- **多模态全栈支持（Multimodal Support）**：统一处理文本、视觉图像与语音音频等多模态数据输入。
- **本地私有化部署（Local Deployment）**：完美支持通过 [Ollama](https://ollama.com/)、[LMStudio](https://lmstudio.ai/) 或 [ONNX](https://onnx.ai/) 进行离线本地化推理。
- **业务流程建模（Process Framework）**：以结构化工作流方法对复杂企业业务流程进行精准建模与控制。
- **企业级生产就绪（Enterprise Ready）**：具备深度的全链路可观测性、健全的安全控制机制以及长期稳定的 API 设计。

## 安装指南 (Installation)

首先，为你的 AI 服务配置对应的环境变量：

**使用 Azure OpenAI：**
```bash
export AZURE_OPENAI_API_KEY=AAA....
```

**或直接使用 OpenAI：**
```bash
export OPENAI_API_KEY=sk-...
```

### Python

```bash
pip install semantic-kernel
```

### .NET

```bash
dotnet add package Microsoft.SemanticKernel
dotnet add package Microsoft.SemanticKernel.Agents.Core
```

### Java

具体构建与依赖说明请参阅 [semantic-kernel-java 构建指南](https://github.com/microsoft/semantic-kernel-java/blob/main/BUILD.md)。

## 快速上手 (Quickstart)

### 基础智能体 - Python

构建一个响应用户提示词的基础智能对话助理：

```python
import asyncio
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

async def main():
    # 使用基础系统指令初始化一个对话智能体
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="SK-Assistant",
        instructions="你是一名乐于助人的 AI 助手。",
    )

    # 获取针对用户消息的回复
    response = await agent.get_response(messages="请为 Semantic Kernel 写一首短诗。")
    print(response.content)

asyncio.run(main()) 

# 输出示例：
# 语义之精粹，
# 逻辑线缕相互交织，
# 顿现智慧核心。
```

### 基础智能体 - .NET

```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

var builder = Kernel.CreateBuilder();
builder.AddAzureOpenAIChatCompletion(
                Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT"),
                Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT"),
                Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY")
                );
var kernel = builder.Build();

ChatCompletionAgent agent =
    new()
    {
        Name = "SK-Agent",
        Instructions = "你是一名乐于助人的 AI 助手。",
        Kernel = kernel,
    };

await foreach (AgentResponseItem<ChatMessageContent> response 
    in agent.InvokeAsync("请为 Semantic Kernel 写一首短诗。"))
{
    Console.WriteLine(response.Message);
}

// 输出示例：
// 语义之精粹，
// 逻辑线缕相互交织，
// 顿现智慧核心。
```

### 带有插件的智能体 - Python

为你的智能体配置自定义工具（插件）与结构化格式输出能力：

```python
import asyncio
from typing import Annotated
from pydantic import BaseModel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.functions import kernel_function, KernelArguments

class MenuPlugin:
    @kernel_function(description="提供菜单上的特价菜品列表。")
    def get_specials(self) -> Annotated[str, "返回菜单中的特价菜品。"]:
        return """
        特价例汤: 蛤蜊浓汤
        特选沙拉: 科布沙拉
        特色饮品: 印度奶茶
        """

    @kernel_function(description="提供指定菜单商品的价格。")
    def get_item_price(
        self, menu_item: Annotated[str, "菜单商品的名称。"]
    ) -> Annotated[str, "返回该菜品的价格。"]:
        return "$9.99"

class MenuItem(BaseModel):
    price: float
    name: str

async def main():
    # 配置结构化输出格式
    settings = OpenAIChatPromptExecutionSettings()
    settings.response_format = MenuItem

    # 使用插件和配置创建智能体
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="SK-Assistant",
        instructions="你是一名乐于助人的餐厅服务助手。",
        plugins=[MenuPlugin()],
        arguments=KernelArguments(settings)
    )

    response = await agent.get_response(messages="今天的特价汤品是多少钱？")
    print(response.content)

    # 输出示例：
    # 今天的特价汤品是蛤蜊浓汤，价格为 $9.99。

asyncio.run(main()) 
```

### 带有插件的智能体 - .NET

```csharp
using System.ComponentModel;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

var builder = Kernel.CreateBuilder();
builder.AddAzureOpenAIChatCompletion(
                Environment.GetEnvironmentVariable("AZURE_OPENAI_DEPLOYMENT"),
                Environment.GetEnvironmentVariable("AZURE_OPENAI_ENDPOINT"),
                Environment.GetEnvironmentVariable("AZURE_OPENAI_API_KEY")
                );
var kernel = builder.Build();

kernel.Plugins.Add(KernelPluginFactory.CreateFromType<MenuPlugin>());

ChatCompletionAgent agent =
    new()
    {
        Name = "SK-Assistant",
        Instructions = "你是一名乐于助人的餐厅服务助手。",
        Kernel = kernel,
        Arguments = new KernelArguments(new PromptExecutionSettings() { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() })
    };

await foreach (AgentResponseItem<ChatMessageContent> response 
    in agent.InvokeAsync("今天的特价汤品是多少钱？"))
{
    Console.WriteLine(response.Message);
}

sealed class MenuPlugin
{
    [KernelFunction, Description("提供菜单上的特价菜品列表。")]
    public string GetSpecials() =>
        """
        特价例汤: 蛤蜊浓汤
        特选沙拉: 科布沙拉
        特色饮品: 印度奶茶
        """ ;

    [KernelFunction, Description("提供指定菜单商品的价格。")]
    public string GetItemPrice(
        [Description("菜单商品的名称。")]
        string menuItem) =>
        "$9.99";
}
```

### 多智能体协同系统 - Python

构建由多个专长智能体相互协作的多 Agent 系统：

```python
import asyncio
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion

# 账单处理专员
billing_agent = ChatCompletionAgent(
    service=AzureChatCompletion(), 
    name="BillingAgent", 
    instructions="你负责处理扣费、支付方式、账单周期、手续费、账单差异及支付失败等账务问题。"
)

# 退款处理专员
refund_agent = ChatCompletionAgent(
    service=AzureChatCompletion(),
    name="RefundAgent",
    instructions="协助用户处理退款咨询，包括退款资格评估、政策解释、流程流转及状态跟踪。",
)

# 分诊调度智能体
triage_agent = ChatCompletionAgent(
    service=OpenAIChatCompletion(),
    name="TriageAgent",
    instructions="评估用户诉求，并精准分发给 BillingAgent 或 RefundAgent 获取针对性协助。"
    " 整合所有智能体给出的信息，向用户提供全面详尽的最终回答。",
    plugins=[billing_agent, refund_agent],
)

thread: ChatHistoryAgentThread = None

async def main() -> None:
    print("欢迎使用客服助手！\n  输入 'exit' 退出聊天。\n  试着咨询账单或退款相关问题。")
    while True:
        user_input = input("User:> ")

        if user_input.lower().strip() == "exit":
            print("\n\n退出会话...")
            return False

        response = await triage_agent.get_response(
            messages=user_input,
            thread=thread,
        )

        if response:
            print(f"Agent :> {response}")

# 输出示例：
# Agent :> 我了解到您上个月的订阅产生了重复扣费，我将协助您解决此问题。接下来我们需要执行以下操作：
# 1. 账务核查：请提供与您订阅绑定的邮箱地址或账户编号、扣费具体日期及扣费金额。账务团队将据此核对收费明细。
# 2. 退款流程：请核实订阅类型，并提供疑似重复扣费的交易单号（Transaction ID）。
# 资料核验无误后，我们将立即为您发起重复款项的原路退还（退款通常在审核通过后 5-10 个工作日内到账）。

if __name__ == "__main__":
    asyncio.run(main())
```

## 进阶探索与参考资料 (Where to Go Next)

1. 📖 阅读官方 [快速入门指南 (Getting Started Guide)](https://learn.microsoft.com/en-us/semantic-kernel/get-started/quick-start-guide) 或了解 [如何构建智能体 (Building Agents)](https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/)
2. 🔌 探索 100+ 涵盖各领域的 [详实示例代码 (Detailed Samples)](https://learn.microsoft.com/en-us/semantic-kernel/get-started/detailed-samples)
3. 💡 深入了解核心 [架构设计与概念 (Concepts)](https://learn.microsoft.com/en-us/semantic-kernel/concepts/kernel)

### API 参考文档

- [C# API 参考手册](https://learn.microsoft.com/en-us/dotnet/api/microsoft.semantickernel?view=semantic-kernel-dotnet)
- [Python API 参考手册](https://learn.microsoft.com/en-us/python/api/semantic-kernel/semantic_kernel?view=semantic-kernel-python)

## 故障排查 (Troubleshooting)

### 常见问题

- **身份认证异常（Authentication Errors）**：检查并确保所配置的 API 密钥及环境变量格式完全正确。
- **模型可用性异常（Model Availability）**：检查 Azure OpenAI 模型部署状态或 OpenAI 账户的模型访问配额权限。

### 获取支持

- 在 [GitHub Issues](https://github.com/microsoft/semantic-kernel/issues) 查阅已知问题与最新进展
- 在官方 [Discord 开发者社区](https://aka.ms/SKDiscord) 交流解决方案
- 寻求帮助时，请务必附带所使用的 SDK 完整版本号及详细的错误堆栈信息

## 加入社区交流

我们真诚欢迎你对 Semantic Kernel 社区提出贡献与宝贵建议！最直接的参与方式之一是在 GitHub 讨论区与我们互动。无论是提交 Bug 报告还是修复 PR，我们都由衷欢迎！

对于计划新增的功能、组件或大型扩展，请在提交 PR 前先开启 Issue 展开充分讨论。这样既能避免因架构路线偏离导致的不必要返工，也能兼顾对更广泛生态系统的影响。

了解更多与开启贡献：

- 阅读官方 [技术文档](https://aka.ms/sk/learn)
- 学习如何向本项目 [参与代码与文档贡献](https://learn.microsoft.com/en-us/semantic-kernel/support/contributing)
- 在 [GitHub Discussions](https://github.com/microsoft/semantic-kernel/discussions) 中提出疑问
- 加入 [Discord 开发者社区](https://aka.ms/SKDiscord) 与全球开发者交流
- 参与 [定期举办的社区答疑日（Office Hours）与开发者活动](COMMUNITY.md)
- 在 [官方博客](https://aka.ms/sk/blog) 关注产品最新动态

## 贡献者名人墙 (Contributor Wall of Fame)

[![semantic-kernel contributors](https://contrib.rocks/image?repo=microsoft/semantic-kernel)](https://github.com/microsoft/semantic-kernel/graphs/contributors)

## 行为准则 (Code of Conduct)

本项目遵循 [微软开源行为准则 (Microsoft Open Source Code of Conduct)](https://opensource.microsoft.com/codeofconduct/)。
如需了解更多信息，请查阅 [行为准则常见问题解答](https://opensource.microsoft.com/codeofconduct/faq/)，
或发送电子邮件至 [opencode@microsoft.com](mailto:opencode@microsoft.com) 咨询相关问题。

## 开源许可证 (License)

Copyright (c) Microsoft Corporation. All rights reserved.

本项目基于 [MIT](LICENSE) 许可证开源发布。

---

> 💡 **文档维护说明**：本中文文档由社区志愿者（@JasonYeYuhe）翻译维护，最后同步更新于 2026年9月8日。如发现内容与官方英文原版存在差异或新特性滞后，欢迎提交 PR 共同完善！
