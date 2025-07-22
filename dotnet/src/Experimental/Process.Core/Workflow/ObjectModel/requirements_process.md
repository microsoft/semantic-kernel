## Process Flavors

#### Types of Processes
- Pro-Code: Developer coded process hosted as a foundry workflow
- Declarative: Process built by interpreting declarative yaml
- Custom: Developer coded process hosted in whatever service they choose

#### Process Comparison
Aspect|Pro-Code|Declarative|Custom
:--|:--:|:--:|:--:
Accepts `ILoggerFactory`|✔|✔|✔
Checkpoint & restore process|✔|✔|✔
Hosted in _Foundry_ |✔|✔|❓
Requires _Foundry_ endpoint|✔|✔|❌
Supports custom steps|✔|❌|✔
Emits execution events|❓|✔|❓

#### Open Questions
- Can _any_ process be hosted in _Foundry_? 
  (Is a "Pro-Code" process and "Custom" process equivalent?)
- Can a "Pro-Code" process be represented as a declarative workflow?  **NO**
- Do execute events need to be emitted for any process?  **YES**
- Can a _Foundry_ workflow be hosted in different projects without modification? **NO**  
  (Agent identifiers differ even if model deployments match.)
- Is a _Foundry_ workfow specific to a single _Foundry_ project? **YES**
