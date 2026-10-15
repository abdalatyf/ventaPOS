# Chapter 2: Architecture Overview & AI Routing

# **Enterprise Blueprint: Orchestrating a 12-Agent Swarm for POS and E-commerce Development in Google Antigravity 2.0**

## **Introduction**

The transition from human-centric software engineering to autonomous multi-agent development requires a fundamental paradigm shift in enterprise system architecture. Constructing a comprehensive Point of Sale (POS) and E-commerce ecosystemâ€”comprising a Django backend, a Bootstrap/Django Template Language (DTL) web dashboard, and a cross-platform Flutter mobile applicationâ€”introduces immense complexities in data synchronization, state management, and continuous integration. Addressing these complexities through a 12-agent automated development swarm necessitates an orchestration layer capable of managing asynchronous parallel execution, enforcing strict data handoffs, and preserving localized context windows without degrading code quality or introducing hallucinatory regressions.  
Google Antigravity 2.0 serves as the foundational operating layer for this advanced architecture1. By deprecating the traditional IDE-bound chatbot model in favor of a standalone multi-agent desktop application and orchestration platform, Antigravity 2.0 enables independent artificial intelligence agents to interact dynamically across discrete enterprise workspaces3. The ecosystem provides an unbundled suite of interfaces, including the desktop Agent Manager for high-level orchestration, a Go-based CLI for headless terminal execution, and a programmatic Python SDK for custom backend pipelines6. This blueprint exhaustively details the deployment of the specified 12-agent development swarm, which is strategically divided into Core Development (Project Manager, UI/UX Designer, Backend Developer, Frontend Developer, Mobile Developer, QA Tester, DevOps Engineer) and AI-Specific Management (Orchestrator, Security/Vulnerability, Database Architect, Mock Data Generator, Documentation). The subsequent analysis delineates state-of-the-art implementations utilizing the Antigravity SDK, the Agent-to-Agent (A2A) protocol, the Model Context Protocol (MCP), Agentic Resource Discovery (ARD), and stringent Human-in-the-Loop (HITL) approval matrices to guarantee production-grade execution for the POS and E-commerce ecosystem.

## **State-of-the-Art Best Practices in Antigravity 2.0**

Orchestrating twelve highly specialized agents demands strict adherence to Antigravity 2.0 architectural paradigms. The platform fundamentally shifts the development model from sequential, human-blocked execution to parallelized autonomous workflows governed by a centralized orchestration layer5.

### **Multi-Agent Parallelism and Subagent Delegation**

In legacy artificial intelligence workflows, the entire pipeline halts while a single model processes an isolated task. Antigravity 2.0 resolves this bottleneck through dynamic subagent delegation and asynchronous execution1. The Orchestrator (The Maestro) functions as the primary routing and synchronization entity, utilizing the native invoke\_subagent capability to spawn concurrent, specialized worker threads9.  
The Orchestrator maintains a high-level view of the POS ecosystem, delegating distinct repositories or feature branches to the Backend (Django) and Mobile (Flutter) developers simultaneously. This parallel execution dramatically increases build momentum, as the Django backend logic and Flutter interface structure evolve concurrently rather than sequentially8. Subagents execute asynchronously in the background, allowing the Orchestrator to continue synchronizing work or resolving architectural conflicts. A subagent exists in one of three states: Running (actively calling tools and generating responses), Paused (waiting for a parent agent's response or human input), or Idle9. To prevent runaway resource exhaustion, Antigravity 2.0 strictly enforces a maximum nesting depth of ten delegation layers9. Furthermore, enterprise environments leveraging the Google AI Ultra plan can utilize the /teamwork-preview framework, which provides built-in error recovery and automatic retries for the multi-agent swarm9.

### **Context Window Management and Compaction**

A pervasive vulnerability in single-agent architectures is context pollution, wherein the accumulation of massive codebases, deployment logs, and API specifications overwhelms the Large Language Model's active memory. This results in degraded reasoning and severe code hallucination. The 12-agent swarm mitigates this through enforced context isolation. When the Orchestrator invokes a subagent, such as the QA/Software Tester or the Security & Vulnerability agent, the subagent does not inherit the Orchestratorâ€™s historical chat transcript9. Instead, it begins with a clean cognitive slate, operating either in a shared workspace or a completely isolated Git worktree9.  
For agents requiring prolonged execution lifecycles, such as the DevOps/Cloud Engineer managing CI/CD pipelines, context preservation is handled by Antigravityâ€™s automatic context compaction. This compaction mechanism is natively triggered when the session reaches approximately 135,000 tokens, supporting multi-turn sessions without losing critical state variables or triggering token limit failures11.

### **State Persistence and Remote Execution Sandboxes**

Enterprise development mandates that an agent's workspace state persists across complex, multi-turn sessions. Utilizing the Antigravity Python SDK, agents can be provisioned within secure, remote Ubuntu sandboxes on Google Cloud infrastructure via the environment="remote" configuration parameter11. This capability is critical for the POS ecosystem's backend development. When the Database Architect finalizes the PostgreSQL schema, the operational state of the sandbox is captured as a unique environment\_id11.  
If the Backend Developer subsequently needs to construct the core logic, generate Django ORM models, and execute python manage.py makemigrations, the Orchestrator directs the Backend Developer to re-attach to that identical environment\_id11. The agent inherits the exact filesystem, installed dependencies, and environmental variables, ensuring seamless continuity. Furthermore, state continuity can be locally preserved by downloading the workspace as a tarball snapshot (snapshot\_env.tar) via the SDK, allowing the entire Django and Flutter development environment to be archived, audited, or duplicated for parallel QA testing environments12.

### **Optimal Cost-Saving Strategies via Algorithmic Model Routing**

Executing a continuous 12-agent swarm exclusively on frontier intelligence models incurs prohibitive API token costs. Cost optimization requires algorithmic model routing governed by specific task complexity10. Within the Antigravity ecosystem, distinct agents utilize specific underlying Gemini models dictated by YAML frontmatter in their operational skill definitions13.  
The cumulative operational cost of the multi-agent system is minimized by routing high-reasoning tasks to frontier models and low-complexity, high-velocity tasks to more efficient models. High-reasoning agents, including the Orchestrator, Database Architect, Backend Developer, and Security/Vulnerability tester, mandate the use of gemini-3.1-pro to ensure architectural soundness, complex API construction, and rigorous penetration testing11. Conversely, high-velocity agents such as the Mock Data Generator, Documentation agent, and Frontend Web Developer operate optimally on gemini-3.5-flash15. The Mock Data Generator executing repetitive INSERT statements or creating dummy JSON payloads does not require deep, systemic reasoning, making the Flash model economically and operationally superior10.

| Swarm Agent | Designated Role | Optimal Model Routing | Execution State |
| :---- | :---- | :---- | :---- |
| **01\. Product/Project Manager** | Requirements, task translation | gemini-3.1-pro | Synchronous / Paused |
| **02\. UI/UX Designer** | Interface, journey, design tokens | gemini-3.5-flash | Asynchronous |
| **03\. Backend Developer** | Django logic, APIs, permissions | gemini-3.1-pro | Asynchronous |
| **04\. Frontend Developer** | Bootstrap/DTL web conversion | gemini-3.5-flash | Asynchronous |
| **05\. Mobile Developer** | Flutter app, real-time syncing | gemini-3.1-pro | Asynchronous |
| **06\. QA/Software Tester** | Bug hunting, edge case testing | gemini-3.5-flash | Scheduled Background |
| **07\. DevOps/Cloud Engineer** | CI/CD, database backups | gemini-3.1-pro | Scheduled Background |
| **08\. Orchestrator (Maestro)** | Synchronization, conflict resolution | gemini-3.1-pro | Always Active |
| **09\. Security & Vulnerability** | Penetration testing, SQLi scans | gemini-3.1-pro | Asynchronous |
| **10\. Database Architect** | Schema and relationships | gemini-3.1-pro | Asynchronous |
| **11\. Mock Data Generator** | Realistic dummy record insertion | gemini-3.5-flash | Asynchronous |
| **12\. Documentation** | Swagger docs, diagrams, ReadMe | gemini-3.5-flash | Asynchronous |

## **Workflow and Data Handoffs**

To assemble a unified POS and E-commerce platform comprising isolated micro-frontends (Flutter, Bootstrap/DTL) and a monolithic backend (Django), data handoffs between agents must rely on rigid semantic contracts. Relying on unstructured natural language for critical architecture handoffs invariably leads to systemic hallucination.

### **Agentic Resource Discovery and The A2A Protocol**

Before data can be passed, agents must locate and verify one another. This is achieved through the Agentic Resource Discovery (ARD) specification, an open protocol for publishing and discovering capabilities across federated registries17. An enterprise ARD registry crawls static ai-catalog.json manifests hosted on the internal network, allowing the Orchestrator to dynamically discover the specific endpoint for the Database Architect or the QA Tester based on natural language intent17.  
Once discovered, communication between the agents utilizes the Agent-to-Agent (A2A) protocol20. A2A is an open standard that relies on JSON-RPC 2.0 over HTTPS and Server-Sent Events (SSE) for secure, stateful messaging22. The remote agent exposes an Agent Cardâ€”a JSON metadata document detailing its identity, capabilities, operations, and authentication requirements20. When the Orchestrator delegates a feature build, it issues a message/send JSON-RPC method containing the task parameters. The receiving agent evaluates this as a Task object, updating its lifecycle state, and eventually returning a structured Artifact payload upon completion without exposing its internal memory or toolset to the Orchestrator21.

### **Semantic Data Passing Formats**

To prevent semantic drift across the POS ecosystem, data passed between agents adheres to specialized serialization formats tailored to the domain.  
When the Database Architect and Backend Developer construct the Django REST Framework endpoints, they expose the service definitions as an OpenAPI 3.1 JSON document. The Orchestrator forwards this highly structured specification directly to the Mobile Developer and Frontend Developer via A2A messaging. This ensures that Dart HTTP clients and DTL AJAX requests map perfectly to the backend, eliminating the hallucination of parameter names or endpoint routes.  
For visual design handoffs, the UI/UX Designer utilizes the Agent-to-User Interface (A2UI) specification. Rather than generating brittle, disjointed HTML or CSS code that the Frontend Developer must interpret, the UI/UX Designer streams a declarative JSON structure abstractly describing the interface components27. This A2UI payload utilizes a predefined component catalog and operates on a native-first philosophy28. The human orchestrator can render this JSON natively via a Flutter or React viewer to verify the POS dashboard design visually. Once approved, the Frontend Developer translates the verified A2UI JSON blueprint into the final Bootstrap and Django templates27.

### **Sequence of Execution and Milestone Mapping**

The automated development of a discrete POS feature, such as a localized inventory tracking module, follows a deterministic pipeline orchestrated via these specific A2A handoffs.

| Execution Phase | Acting Swarm Agent | Action Performed | Output Data Format |
| :---- | :---- | :---- | :---- |
| **1\. Requirements** | Product/Project Manager | Analyzes user requests, defines business logic. | Technical\_Specification.md \[cite: 30\] |
| **2\. Architecture** | Database Architect | Designs relational schema and Django ORM models. | SQL DDL, openapi.json \[cite: 22\] |
| **3\. Interface** | UI/UX Designer | Formulates user journeys and dashboard layouts. | A2UI Declarative JSON28 |
| **4\. Core Logic** | Backend Developer | Constructs models.py, views.py, DRF Serializers. | Python source code, Django Migrations |
| **5\. Integration** | Frontend & Mobile Devs | Connects Flutter Dart models and DTL templates to APIs. | Dart source code, HTML/JS/CSS |
| **6\. Verification** | QA Tester & Mock Data | Populates DB via SQL, runs PyTest and Flutter Test. | QA Walkthrough, coverage reports31 |
| **7\. Hardening** | Security & Vulnerability | Executes penetration tests (SQLi, Auth bypass). | Security Audit Report |
| **8\. Deployment** | DevOps/Cloud Engineer | Packages infrastructure, updates CI/CD pipelines. | Dockerfile, docker-compose.yml |

## **Tool Provisioning and Environment Isolation**

Agents within Google Antigravity 2.0 require programmatic access to compilers, database engines, and operating systems to validate their generated code. This access must be rigorously sandboxed and permissioned to prevent catastrophic system degradation.

### **Model Context Protocol (MCP) Integration**

While the A2A protocol acts as the horizontal coordination layer between the agents, the Model Context Protocol (MCP) serves as the vertical connection layer between an individual agent and its external operational environment22. MCP provides a standardized mechanism for agents to interface with external tools, databases, and APIs without custom wiring22.  
Within the POS deployment, the Database Architect and Mock Data Generator are provisioned with an MCP server connected directly to an isolated PostgreSQL container. This configuration allows the agents to execute raw SQL queries, verify Django schema migrations, and run vast INSERT statements to populate the database natively, rather than generating unverified syntax32. The Mobile Developer is provisioned with an MCP server wrapper around the Flutter CLI, granting the agent the capability to execute flutter run, flutter build, and perform hot-reloads directly within the container to verify widget rendering32. Similarly, the DevOps engineer leverages a Docker MCP server to validate the orchestration of the .env, PostgreSQL, Redis, Django, and frontend services within the docker-compose.yml network.

### **Antigravity SDK Policy Hooks and Read/Write Permissions**

The Principle of Least Privilege is strictly enforced using the Antigravity Python SDK's declarative policy system33. The LocalAgentConfig module enables architects to define precise read, write, and execution parameters using the deny, allow, and ask\_user hooks33.  
To prevent the artificial intelligence from arbitrarily wiping directories or pushing untested code to production repositories, the environment is provisioned with a highly restrictive policy matrix. The agent runtime configuration defaults to denying all tool access, selectively enabling read permissions across the workspace to facilitate codebase comprehension. Write access is restricted to specific source directories via regex path matching. Crucially, any attempt to execute a shell commandâ€”such as running a build script, executing a database migration, or initiating a repository pushâ€”is intercepted by the ask\_user hook. This interception halts the agent's autonomous execution and triggers a mandatory human approval workflow, ensuring that systemic modifications cannot occur without cryptographic or manual authorization33.

### **Docker Sandboxes and Environment Independence**

Antigravity 2.0 natively supports fully isolated execution environments. When executing code, the native code\_execution tool operates within a secure Ubuntu container on Google Cloud, capturing stdout and stderr outputs11. Because the agents interact with the POS application network via MCP and Antigravity's native tools, any erroneous code generated by the Backend Developer or destructive penetration tests executed by the Security Tester are completely localized. The disposable container architecture ensures that underlying host machines are shielded from arbitrary code execution vulnerabilities or runaway processes initiated by the swarm11.

## **Anti-Hallucination Guardrails and System Prompts**

Large Language Models are inherently prone to probabilistic drift, which in enterprise development translates into infinite coding loops, recursive error generation, and deviation from core requirements. The 12-agent swarm relies on deterministic rule mechanisms, progressive disclosure via agent skills, and automated local verification loops to neutralize these hallucinations.

### **Structuring AGENTS.md for Global Guardrails**

Antigravity 2.0 natively parses global rule files located at the root of a workspace repository, conventionally named AGENTS.md or GEMINI.md4. This file functions as the overarching system prompt, injecting crucial constraints and architectural context into the active memory of every agent immediately upon startup36.  
For the POS and E-commerce platform, the AGENTS.md file explicitly outlines the architectural standards. It defines the technology stack, strictly prohibiting the use of alternative frameworks when Django and Flutter are mandated. It enforces coding paradigms, such as strict PEP 8 compliance for Python backend logic and modern asynchronous state management patterns for Dart. Furthermore, the AGENTS.md file defines the specific personas of the 12-agent team via designated Goals, Traits, and Constraints30. A foundational constraint deployed across all agents mandates that they must always pause for explicit approval prior to considering a task complete, and must never overwrite existing code without first generating and securing approval for an Implementation Plan Artifact30.

### **Progressive Disclosure via the Skills Architecture**

To prevent system prompt bloatâ€”which directly degrades an agent's reasoning performanceâ€”Antigravity utilizes a progressive disclosure architecture housed within a dedicated skills/ directory30. Rather than loading all conceivable operational instructions into the main context window, capabilities are modularized as individual Markdown frontmatter files, such as audit\_code.md or deploy\_app.md30.  
When the Orchestrator tasks the QA/Software Tester with evaluating a newly developed Django application module, the QA agent dynamically loads the audit\_code.md skill30. This skill dictates a rigid procedural loop: the agent must assess the raw code against the approved Technical\_Specification.md, hunt for unhandled errors, execute the PyTest suite, and if an error is detected, analyze the traceback to generate a fix30. The prompt-generate-validate loop ensures the agent continuously verifies its output against local test results, self-correcting based on compiler feedback11.

### **Loop Prevention and Checkpointing**

To prevent infinite debugging loops, the skills architecture dictates that an agent must halt execution and request human intervention upon consecutive test failures exceeding a defined threshold. Furthermore, to mitigate the risk of destructive overwrites, Antigravity 2.0 incorporates native History Rewind and Checkpointing. If the Frontend Developer introduces cascading syntax errors into the Bootstrap components, the human architect can utilize the /rewind or /undo command in the CLI or Agent Manager to seamlessly roll back the conversation thread and the associated file states to a previous, stable checkout36. Parallel experimentation is handled by the /fork command, which allows the Orchestrator to branch the conversation, testing alternative Django architectural paths without polluting the primary workspace36.

## **Human-in-the-Loop (HITL) Optimization**

Despite the advanced autonomy of the 12-agent swarm, production-grade enterprise software necessitates a strict Human-in-the-Loop (HITL) architecture. The objective is to elevate the human architect from a passive auditor of machine-generated code into an executive decision-maker overseeing deterministic milestones3.

### **Designing Approval Gates**

Approval gates are programmatic hard-stops integrated directly into the Antigravity SDK and the multi-agent workflow. Utilizing the SDK's ask\_user policy, critical infrastructure modifications are structurally prevented from auto-executing33.  
Within the POS ecosystem, three primary approval gates are mandatory:

1. **Schema Finalization Gate:** Prior to executing database migrations, the Database Architect must present the Entity-Relationship Diagram and SQL DDL scripts. The Orchestrator intercepts the process, pausing the workflow until the human architect physically inputs an approval command, ensuring foundational data structures are flawless30.  
2. **UI Integration Gate:** The UI/UX designer generates the initial visual layout utilizing the A2UI protocol. Because A2UI relies on a JSON payload describing intent rather than raw code, the host application securely renders the interface using native elements27. Once the human architect approves the visual structure through this secure rendering, the Orchestrator signals the Frontend and Mobile developers to begin writing the underlying Bootstrap/DTL and Flutter code.  
3. **Merging and Deployment Gate:** The DevOps and Security agents complete their audits, outputting final reports. The critical action of merging the verified code into the primary deployment branch triggers an ask\_user("git\_push") SDK policy, requiring final cryptographic or manual sign-off before the POS system is updated33.

### **Orchestrator Summaries and Artifact Generation**

Evaluating raw code diffs generated by a 12-agent swarm is highly inefficient for human review. Antigravity 2.0 addresses this by translating agent outputs into highly structured, scannable deliverables known as Artifacts2.  
The Orchestrator agent compiles the outputs of the PM, DB Architect, Developers, and Testers into unified Artifacts:

* **Task Lists:** Generated prior to code execution, structuring the agent's intended plan of action for human review31.  
* **Implementation Plans:** Detailed architectural blueprints containing technical specifics on necessary revisions, ensuring human overseers can perform impact analysis before files are overwritten31.  
* **Screenshots and Visuals:** The UI/UX and Mobile agents utilize browser tools and Flutter execution emulators to capture the visual state of the application before and after changes, attaching explicit visual evidence31.  
* **Walkthroughs:** A post-execution summary detailing the systemic changes made, the bugs resolved, and instructions on how to manually verify the functionality31.

By funneling the swarm's output through these structured Artifacts, the Orchestrator presents the human architect with comprehensive summaries that are immediately ready for deployment authorization32. Furthermore, routine maintenance tasks, such as the QA tester running edge-case simulations or the DevOps engineer backing up the PostgreSQL database, are transitioned to Scheduled Tasks. Utilizing cron-like automation, these background agents execute autonomously on a defined schedule, transforming AI from a basic coding assistant into autonomous operational infrastructure1.

## **Conclusion**

The deployment of a comprehensive POS and E-commerce ecosystem utilizing Django, Bootstrap/DTL, and Flutter is profoundly accelerated through the Google Antigravity 2.0 orchestration platform. By segmenting complex architectural responsibilities across a 12-agent swarm, enterprise architects eliminate the sequential bottlenecks and context pollution characteristic of legacy AI coding interactions. Success within this paradigm hinges on rigid architectural discipline and the adoption of open protocols. The integration of Agent-to-Agent (A2A) messaging ensures deterministic data handoffs, while Model Context Protocol (MCP) servers grant agents the secure, sandboxed execution environments required to validate code locally. Ultimately, the enforcement of programmatic policy hooks, AGENTS.md behavioral constraints, and declarative Artifact generation ensures that the multi-agent swarm operates strictly within safe, enterprise-grade boundaries, empowering the human architect to oversee rapid, production-scale software development with unparalleled efficiency and control.

#### **Works cited**

1. Google AntiGravity 2.0 : Bye Claude Code | by Mehul Gupta | Data Science in Your Pocket, [https://medium.com/data-science-in-your-pocket/google-antigravity-2-0-bye-claude-code-f13fd82ffb0e](https://medium.com/data-science-in-your-pocket/google-antigravity-2-0-bye-claude-code-f13fd82ffb0e)  
2. Antigravity 2.0, [https://antigravity.google/product/antigravity-2](https://antigravity.google/product/antigravity-2)  
3. Google Antigravity 2.0 replaced the IDE behind a chatbotâ€”but you can get it back, [https://www.howtogeek.com/google-antigravity-hid-the-ide-behind-a-chatbot-heres-how-to-get-it-back/](https://www.howtogeek.com/google-antigravity-hid-the-ide-behind-a-chatbot-heres-how-to-get-it-back/)  
4. The Hitchhiker's Guide to Antigravity 2.0 | by Daniela Petruzalek | Google Cloud \- Medium, [https://medium.com/google-cloud/the-hitchhikers-guide-to-antigravity-2-0-af17eb4845c0](https://medium.com/google-cloud/the-hitchhikers-guide-to-antigravity-2-0-af17eb4845c0)  
5. Parallel agents in Antigravity \- Google Cloud \- Medium, [https://medium.com/google-cloud/parallel-agents-in-antigravity-64237120161d](https://medium.com/google-cloud/parallel-agents-in-antigravity-64237120161d)  
6. Choosing your surface: Antigravity 2.0, Antigravity CLI, Antigravity IDE, or Antigravity SDK | Google Cloud Blog, [https://cloud.google.com/blog/topics/developers-practitioners/choosing-your-surface-antigravity-20-antigravity-cli-antigravity-ide-or-antigravity-sdk](https://cloud.google.com/blog/topics/developers-practitioners/choosing-your-surface-antigravity-20-antigravity-cli-antigravity-ide-or-antigravity-sdk)  
7. An important update: Transitioning Gemini CLI to Antigravity CLI \- Google Developers Blog, [https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/](https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/)  
8. Google Antigravity Multi Agent Workflow Removes Coding Bottlenecks \- Reddit, [https://www.reddit.com/r/AISEOInsider/comments/1s0tz91/google\_antigravity\_multi\_agent\_workflow\_removes/](https://www.reddit.com/r/AISEOInsider/comments/1s0tz91/google_antigravity_multi_agent_workflow_removes/)  
9. Asynchronous Subagents \- Google Antigravity Documentation, [https://antigravity.google/docs/subagents](https://antigravity.google/docs/subagents)  
10. Antigravity Cluster: Google's NEW Free Antigravity Feature MAKES it INSANE\!, [https://www.youtube.com/watch?v=1CeX-Bwv-WY](https://www.youtube.com/watch?v=1CeX-Bwv-WY)  
11. Antigravity Agent | Gemini API \- Google AI for Developers, [https://ai.google.dev/gemini-api/docs/antigravity-agent](https://ai.google.dev/gemini-api/docs/antigravity-agent)  
12. Orchestrating with Antigravity: A Crescendo of Agents (Part 1\) | by Riccardo Carlesso | Jun, 2026 | Medium, [https://medium.com/@palladiusbonton/orchestrating-with-antigravity-a-crescendo-of-agents-part-1-b708b132b8a9](https://medium.com/@palladiusbonton/orchestrating-with-antigravity-a-crescendo-of-agents-part-1-b708b132b8a9)  
13. \[Feature Request\] Native support for YAML model routing and tool loading in Skills via invoke\_subagent \#335 \- GitHub, [https://github.com/google-antigravity/antigravity-cli/issues/335](https://github.com/google-antigravity/antigravity-cli/issues/335)  
14. Release Notes \- Tabnine Docs, [https://docs.tabnine.com/main/administering-tabnine/release-notes](https://docs.tabnine.com/main/administering-tabnine/release-notes)  
15. Google Antigravity \- Wikipedia, [https://en.wikipedia.org/wiki/Google\_Antigravity](https://en.wikipedia.org/wiki/Google_Antigravity)  
16. I/O 2026 developer highlights: Antigravity, Gemini API, AI Studio \- Google Blog, [https://blog.google/innovation-and-ai/technology/developers-tools/google-io-2026-developer-highlights/](https://blog.google/innovation-and-ai/technology/developers-tools/google-io-2026-developer-highlights/)  
17. Announcing the Agentic Resource Discovery specification \- Google Developers Blog, [https://developers.googleblog.com/announcing-the-agentic-resource-discovery-specification/](https://developers.googleblog.com/announcing-the-agentic-resource-discovery-specification/)  
18. Google publishes Agentic Resource Discovery specification | Let's Data Science, [https://letsdatascience.com/news/google-publishes-agentic-resource-discovery-specification-c80b3e40](https://letsdatascience.com/news/google-publishes-agentic-resource-discovery-specification-c80b3e40)  
19. Inside ARD: How the Agentic Resource Discovery Spec Actually Works \- Medium, [https://medium.com/@snowflakechronicles/inside-ard-how-the-agentic-resource-discovery-spec-actually-works-ba61be007942](https://medium.com/@snowflakechronicles/inside-ard-how-the-agentic-resource-discovery-spec-actually-works-ba61be007942)  
20. Getting Started with Agent2Agent (A2A) Protocol: A Purchasing Concierge and Remote Seller Agent Interactions on Cloud Run and Agent Engine | Google Codelabs, [https://codelabs.developers.google.com/intro-a2a-purchasing-concierge](https://codelabs.developers.google.com/intro-a2a-purchasing-concierge)  
21. How A2A is Building a World of Collaborative Agents \- Google Developers Blog, [https://developers.googleblog.com/how-a2a-is-building-a-world-of-collaborative-agents/](https://developers.googleblog.com/how-a2a-is-building-a-world-of-collaborative-agents/)  
22. Google A2A Protocol: How Agent-to-Agent Coordination Works \- Atlan, [https://atlan.com/know/google-a2a-protocol/](https://atlan.com/know/google-a2a-protocol/)  
23. A2A Protocol Specification (Python) | by SiennaV | Medium, [https://medium.com/@vampirenalan/a2a-protocol-specification-python-0df3cfe67bec](https://medium.com/@vampirenalan/a2a-protocol-specification-python-0df3cfe67bec)  
24. A2A/docs/specification.md at main \- GitHub, [https://github.com/a2aproject/A2A/blob/main/docs/specification.md](https://github.com/a2aproject/A2A/blob/main/docs/specification.md)  
25. How to enhance Agent2Agent (A2A) security | Red Hat Developer, [https://developers.redhat.com/articles/2025/08/19/how-enhance-agent2agent-security](https://developers.redhat.com/articles/2025/08/19/how-enhance-agent2agent-security)  
26. A2A JSON-RPC \- Docs by LangChain, [https://docs.langchain.com/langsmith/agent-server-api/a2a/a2a-json-rpc](https://docs.langchain.com/langsmith/agent-server-api/a2a/a2a-json-rpc)  
27. A2UI \+ MCP Apps: Combining the best of declarative and custom agentic UIs, [https://developers.googleblog.com/a2ui-and-mcp-apps/](https://developers.googleblog.com/a2ui-and-mcp-apps/)  
28. A2UI vs. MCP-UI: Comparison of User Interfaces for Agentic AI \- innFactory AI Consulting, [https://innfactory.ai/en/blog/a2ui-vs-mcp-ui-comparison-of-user-interfaces-for-agentic-ai/](https://innfactory.ai/en/blog/a2ui-vs-mcp-ui-comparison-of-user-interfaces-for-agentic-ai/)  
29. A2UI v0.9: What's New in Google's Generative UI Spec | Blog \- CopilotKit, [https://www.copilotkit.ai/blog/a2ui-whats-new-in-google-generative-ui-spec](https://www.copilotkit.ai/blog/a2ui-whats-new-in-google-generative-ui-spec)  
30. Build Autonomous Developer Pipelines using agents.md and skills.md in Antigravity, [https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity](https://codelabs.developers.google.com/autonomous-ai-developer-pipelines-antigravity)  
31. Getting Started with Google Antigravity, [https://codelabs.developers.google.com/getting-started-google-antigravity](https://codelabs.developers.google.com/getting-started-google-antigravity)  
32. Agent Factory Recap: 100X engineering with AI agents in Google Antigravity 2.0, [https://cloud.google.com/blog/topics/developers-practitioners/agent-factory-recap-100x-engineering-with-ai-agents-in-google-antigravity-20](https://cloud.google.com/blog/topics/developers-practitioners/agent-factory-recap-100x-engineering-with-ai-agents-in-google-antigravity-20)  
33. SDK Overview \- Google Antigravity Documentation, [https://antigravity.google/docs/sdk-overview](https://antigravity.google/docs/sdk-overview)  
34. Google Antigravity SDK \- GitHub, [https://github.com/google-antigravity/antigravity-sdk-python](https://github.com/google-antigravity/antigravity-sdk-python)  
35. Antigravity Managed Agents Tutorial: Ship Production AI Agents, [https://medium.com/google-cloud/antigravity-managed-agents-tutorial-ship-production-ai-agents-b5917844932b](https://medium.com/google-cloud/antigravity-managed-agents-tutorial-ship-production-ai-agents-b5917844932b)  
36. Best practices for Antigravity CLI, [https://antigravity.google/docs/cli-best-practices](https://antigravity.google/docs/cli-best-practices)  
37. AGENTS.md, [https://agents.md/](https://agents.md/)  
38. Skills over System Prompts: Building an Anki Tutor with the Antigravity SDK, [https://dev.to/gde/skills-over-system-prompts-building-an-anki-tutor-with-the-antigravity-sdk-2o8f](https://dev.to/gde/skills-over-system-prompts-building-an-anki-tutor-with-the-antigravity-sdk-2o8f)
