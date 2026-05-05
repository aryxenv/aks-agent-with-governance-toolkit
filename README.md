# AKS MAF Weather Agent with Governance Toolkit

> [!IMPORTANT]
> Just a learning project.

Agent server deployed on AKS with a frontend, a server running the weather agent using nomatim for location coordinates and openmeteo for live weather.

## Agent

Microsoft Agent Framework agent declared in [agent](./agent/) with a FastAPI wrapper to expose it as a server.

## Policy

[Policy sidecar](./policy/) for the agent to set deterministic agent policies with [Microsoft Agent Governance Toolkit](https://github.com/microsoft/agent-governance-toolkit).

## Client

Lightweight [frontend](./client/) to chat with the agent.

## k8s

[Kubernetes](./k8s/) stuff for AKS.

## Learning

Want to try this yourself? Here's a visual learning guide to create a fully functional agent on AKS using MAF and AGT [here](./LEARNING.md).
