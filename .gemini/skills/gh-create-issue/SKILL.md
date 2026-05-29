---
name: gh-create-issue
description: Creates a GitHub issue using the 'gh' CLI. The main body contains ONLY the User Story (US). PRD and SPEC details are added as separate comments within the same issue. Use when formalizing specific features into GitHub.
---

# GH Create Issue Skill

This skill formalizes a User Story (US) into a GitHub Issue, keeping the main description focused on the user value and placing technical/product details in comments.

## <instructions>

1. **Granularity Check:**
   Ensure the User Story is atomic. For example, instead of one "Authentication" US, use separate stories for "Login", "Account Creation", and "Social Login".

2. **Draft the Content:**
   - **Main Body (US):** Use the standard format (As a... I want... So that...) and BDD scenarios.
   - **PRD Comment:** Focus on business goals, UI changes, and business rules.
   - **SPEC Comment:** Focus on architecture, data models, APIs, and performance.

3. **Execution Steps:**
   - Create the issue with the US body:
     ```bash
     ISSUE_URL=$(gh issue create --title "[US] Title" --body "USER_STORY_CONTENT")
     ```
   - Add the PRD comment:
     ```bash
     gh issue comment "$ISSUE_URL" --body "PRD_CONTENT"
     ```
   - Add the SPEC comment:
     ```bash
     gh issue comment "$ISSUE_URL" --body "SPEC_CONTENT"
     ```

4. **Consistency:**
   Always use Portuguese (PT-BR) and follow the project's Markdown templates.

</instructions>
