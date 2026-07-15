# Query Interface Test Plan

## Application Overview

The local web interface submits Indonesian financial-regulation questions to the same-origin API, renders citation-first answer states, links to exact source blocks, and records optional feedback without exposing internal query traces.

## Test Scenarios

### 1. Answer states

**Seed:** `e2e/seed.spec.ts`

#### 1.1. answerable

**File:** `e2e/query/answerable.spec.ts`

**Steps:**

1. Ask a question backed by direct BI evidence.
   - expect: The answer is labeled `Jawaban ditemukan`.
   - expect: Strong confidence, answer text, and citation metadata match the API response.

#### 1.2. partial

**File:** `e2e/query/partial.spec.ts`

**Steps:**

1. Ask for a BI and OJK comparison where only BI has direct evidence.
   - expect: The answer is labeled `Jawaban sebagian`.
   - expect: The response states that direct OJK evidence was not found.

#### 1.3. not-found

**File:** `e2e/query/not-found.spec.ts`

**Steps:**

1. Ask a question outside the local regulation corpus.
   - expect: The answer is labeled `Tidak ditemukan`.
   - expect: The interface preserves the API refusal wording and shows no citations.

### 2. Citation navigation

**Seed:** `e2e/seed.spec.ts`

#### 2.1. citation-navigation

**File:** `e2e/query/citation-navigation.spec.ts`

**Steps:**

1. Submit an answerable question.
2. Open its citation link.
   - expect: A new page opens the exact document-block API URL.
   - expect: The API response contains the cited source text.

### 3. Feedback

**Seed:** `e2e/seed.spec.ts`

#### 3.1. feedback-submission

**File:** `e2e/query/feedback-submission.spec.ts`

**Steps:**

1. Submit an answerable question and enter an optional comment.
2. Submit not-helpful feedback.
   - expect: The API receives the query request ID, helpful flag, and comment.
   - expect: The interface confirms that feedback was recorded locally.
