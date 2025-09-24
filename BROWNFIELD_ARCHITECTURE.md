# SpecMint Brownfield Architecture Document

## Introduction

This document captures the CURRENT STATE of the **SpecMint** codebase, including technical debt, workarounds, and real-world patterns. It serves as a reference for AI agents and senior developers working on bug fixes, feature additions, and testing.

### Document Scope

This documentation is a comprehensive analysis of the entire system, with a specific focus on areas relevant to the planned **monetization** enhancement and the **QA/DevOps** pipeline.

### Change Log

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2025-09-02 | 1.0 | Initial brownfield analysis based on PRD and user feedback | Winston (Architect Agent) |

-----

## Quick Reference - Key Files and Entry Points

### Critical Files for Understanding the System

  - **Main Entry**: `src/main.py` (or similar for FastAPI)
  - **Authentication**: `src/auth/clerk.py` (critical area with known issues)
  - **Generation Pipeline**: `src/workers/generator.py` (the core business logic)
  - **Billing/Plans**: `src/billing/` (target area for monetization work)
  - **CI/CD Configuration**: `.github/workflows/ci.yml` (known to be unreliable)

-----

## High-Level Architecture

### Technical Summary

The system is a micro-SaaS with a full-stack design. The backend is built with **FastAPI** using **Python**, a **React** frontend, and a **Redis** queue for asynchronous tasks.

### Actual Tech Stack (from package.json/requirements.txt)

| Category | Technology | Version | Notes |
| :--- | :--- | :--- | :--- |
| Runtime | Python | 3.10+ | |
| Backend Framework | FastAPI | | |
| Frontend | React | | |
| Queue | Redis | | Used for priority queues and daily counters |
| Storage | S3-compatible | | For storing generated ZIP files and artifacts |
| Auth | Clerk | | **Critical: Known issues with authentication and signup** |
| Billing | Lemon Squeezy / Stripe | | Webhooks are key to entitlement |

### Repository Structure Reality Check

  - **Type**: Polyrepo (or similar based on user's setup)
  - **Package Manager**: `pip` and `npm`/`yarn`
  - **Notable**: Separation of frontend and backend codebases is likely.

-----

## Source Tree and Module Organization

### Project Structure (Actual)

```text
project-root/
├── backend/
│ ├── src/
│ │ ├── auth/       # Clerk integration (known issues here)
│ │ ├── services/   # Business logic
│ │ ├── api/        # FastAPI endpoints
│ │ ├── workers/    # Generation and queue workers
│ │ └── models/     # Data models
│ ├── tests/
│ ├── requirements.txt
│ └── ...
├── frontend/
│ ├── src/
│ ├── package.json
│ └── ...
└── .github/
  └── workflows/  # CI/CD scripts (known to be unreliable)
```

### Key Modules and Their Purpose

  - **Authentication**: `backend/src/auth/clerk.py` - Manages user sign-in and signup. **This is a known point of failure.**
  - **Generation Pipeline**: `backend/src/workers/generator.py` - The core AI-driven logic for creating test cases and data.
  - **Billing**: `backend/src/billing/` - Handles plans, quotas, and entitlements. This is the primary area for the upcoming monetization work.

-----

## Technical Debt and Known Issues

### Critical Technical Debt

1.  **CI/CD Pipeline**: The CI workflow (`.github/workflows/ci.yml`) is not reliable and often fails, leading to broken deployments.
2.  **Clerk Auth/Signup**: The authentication and signup functionality is not working correctly, which is a major blocker for user acquisition.

### Workarounds and Gotchas

  - Manual intervention is often required to get a working build to production due to CI failures.
  - Testing is not consistently integrated into the deployment process, leading to functionality breaking in production.

-----

## Development and Deployment

### Build and Deployment Process

  - The CI/CD pipeline is unreliable. Deployments often bypass full testing, which is likely a cause of the "broken functionality" you've noted.
  - The system is deployed via **Fly.io**, which uses a rolling/canary deploy strategy. Failures are often related to the build phase rather than the deployment itself.

-----

## If Enhancement PRD Provided - Impact Analysis

### Files That Will Need Modification

The planned monetization enhancement will directly impact the following areas:

  - **Billing/Plans**: `backend/src/billing/` will need to be expanded to handle add-ons, different subscription tiers, and robust webhook processing from your billing provider.
  - **Quotas**: The Redis-based daily quota counters will need to be adjusted or expanded to support new monetization logic.
  - **User/Auth**: The user model will need new fields to track subscription status, plan type, and other billing-related data.

### New Files/Modules Needed

  - New billing-related API endpoints (e.g., `POST /api/billing/subscribe`).
  - Additional webhook handlers for billing events (e.g., subscription activated/canceled).

### Integration Considerations

  - The new monetization logic must be tightly integrated with the existing authentication system to ensure user entitlements are correctly applied. This is especially critical given the known issues with Clerk.

-----

## Appendix - Useful Commands and Scripts

### Frequently Used Commands

*(This section should be filled in by the user or an agent with access to the codebase. Below are common examples.)*

```bash
# Example
# To start the backend development server
npm run dev:backend

# To run tests
pytest
```

-----

You can copy this document and save it as `docs/brownfield-architecture.md` in your project's repository. This single document now contains all the necessary architectural information for future development.