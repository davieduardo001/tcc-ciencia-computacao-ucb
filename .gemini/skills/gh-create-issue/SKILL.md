---
name: gh-create-issue
description: Creates a GitHub issue using the 'gh' CLI containing a User Story, Technical Specification (SPEC), and Product Requirements Document (PRD). Use when asked to create an issue, translate a User Story into an issue, or formalize a feature request into a GitHub Issue.
---

# GH Create Issue Skill

This skill guides you through formalizing a User Story (US) into a complete, actionable GitHub Issue using the `gh` CLI. It ensures that every issue contains not just the user-centric requirements (US), but also the business expectations (PRD) and technical implementation details (SPEC).

## <instructions>

When tasked with creating an issue based on a User Story or feature request, follow these steps:

1. **Analyze the Request:**
   Understand the base User Story provided by the user. If the user only provides an idea, draft a User Story following standard BDD (Given/When/Then) format first.

2. **Draft the PRD (Product Requirements Document):**
   Determine the business and product requirements for this feature.
   - What UI/UX changes are needed?
   - What is the business logic?
   - What are the success metrics or core value additions?

3. **Draft the SPEC (Technical Specification):**
   Determine how this feature will be built technically.
   - What new APIs, endpoints, or data models are needed?
   - Are there any architectural constraints or performance requirements?
   - What components need to be altered or created?

4. **Prepare the Issue Content:**
   Read the template at `assets/issue_template.md`. Fill it in completely using the US, PRD, and SPEC you drafted. Save this content to a temporary markdown file (e.g., `.gemini/tmp_issue.md`).

5. **Create the GitHub Issue:**
   Use the `run_shell_command` tool to execute the `gh` CLI command:
   ```bash
   gh issue create --title "[Feature/US] Your Concise Title" --body-file .gemini/tmp_issue.md
   ```
   *Note: Ensure the repository has GitHub Issues enabled and the user is authenticated with `gh`. If `gh` is not installed or authenticated, inform the user.*

6. **Cleanup:**
   Delete the temporary markdown file after the issue is successfully created.

</instructions>

## <available_resources>
- `assets/issue_template.md`: The markdown template structure that MUST be used for the issue body.
</available_resources>
