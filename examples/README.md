# Example Agents

This directory contains reference implementations demonstrating different patterns for building agents with the IBM watsonx Orchestrate ADK.

## Available Examples

### 1. Agent Scheduler (`agent_scheduler/`)

A scheduling agent that demonstrates:
- Calendar integration patterns
- Time-based task management
- Multi-step workflow orchestration

**Quick Start:**
```bash
cd agent_scheduler
./import-all.sh
orchestrate chat start agent_scheduler
```

### 2. Customer Care Planner (`customer_care_planner/`)

A customer service agent that demonstrates:
- Planner-style agent architecture
- Customer interaction workflows
- Issue tracking and resolution patterns

**Quick Start:**
```bash
cd customer_care_planner
./import-all.sh
orchestrate chat start customer_care_agent
```

## Structure

Each example follows the same structure as the main workshop project:

```
example_name/
├── agents/           # Agent YAML configurations
├── tools/            # Python tool implementations
├── import-all.sh     # Deployment script
└── README.md         # Example-specific documentation
```

## Using These Examples

1. **Study the patterns**: Review how tools and agents are structured
2. **Compare approaches**: See different ways to solve similar problems
3. **Copy and modify**: Use as templates for your own agents

## Back to Main Workshop

See the main [README.md](../README.md) for the complete workshop guide.
