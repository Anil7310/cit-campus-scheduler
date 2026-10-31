# CIT Scheduling & Venue Management Platform — Architecture Documentation

## 1. System Overview & Core Tenets

The CIT Campus Scheduling Platform is structured into four decoupled layers:
1. **Interactive Client (Frontend):** React 18 SPA with TypeScript and Tailwind CSS.
2. **API & Security Gateway (Backend):** FastAPI with Pydantic v2 schemas and strict role-based access control.
3. **Discrete Optimization Engine:** Google OR-Tools CP-SAT integer programming solver.
4. **Data & Audit Persistence:** MongoDB Atlas with an automatic in-memory fallback for offline test and demo execution.

---

## 2. Mathematical Optimization Architecture (OR-Tools CP-SAT)

The optimization subsystem is housed in [`backend/app/scheduler/`](file:///d:/TTMS/backend/app/scheduler/):

### A. Decision Variables
For each session $s \in S$, we define:
- $D_s \in \{0, \dots, 4\}$: Day index (`MON` to `FRI`).
- $P_s \in \{1, \dots, 9 - \text{duration}(s) + 1\}$: Start period index.
- $R_s \in \{0, \dots, |R|-1\}$: Assigned venue index.

Boolean indicator variables $X_{s, d, p, r} \in \{0, 1\}$ represent whether session $s$ is actively occupying venue $r$ on day $d$ during period $p$.

### B. Hard Constraints (Zero-Tolerance)
1. **No Faculty Clashes:**
   $$\sum_{s \in S_{\text{faculty}(f)}} X_{s, d, p, r} \le 1 \quad \forall f, d, p$$
2. **No Student Group Clashes:**
   $$\sum_{s \in S_{\text{group}(g)}} X_{s, d, p, r} \le 1 \quad \forall g, d, p$$
3. **No Room Overlaps:**
   $$\sum_{s \in S} X_{s, d, p, r} \le 1 \quad \forall r, d, p$$
4. **Room Type Compliance:**
   Labs can only be assigned to $r$ where $\text{type}(r) = \text{LAB}$. Lectures cannot be assigned to LABs.
5. **Continuous Multi-Period Blocks:**
   Lab sessions are scheduled as contiguous 2-hour blocks without splitting.
6. **Lunch Break Protection:**
   Period 5 (12:00 PM – 1:00 PM) is protected; no lecture or lab may bridge across or violate lunch rules.
7. **Daily Faculty Load Ceilings:**
   No faculty member exceeds 4 teaching hours on any single day.
8. **Elective Basket Alignment:**
   Sessions belonging to the same basket slot (e.g. `BASKET-Y3-CSE-SLOT1`) share synchronized day and period decision variables:
   $$D_{s_1} = D_{s_2}, \quad P_{s_1} = P_{s_2} \quad \forall s_1, s_2 \in \text{Basket}$$

### C. Soft Optimization Objectives
$$\min \quad W_{\text{spread}} \cdot \text{FacultySpreadPenalty} + W_{\text{gaps}} \cdot \text{StudentGaps} + W_{\text{afternoon}} \cdot \text{LateDayLoad}$$

---

## 3. Security, Safety, and Governance

- **Anti-Self-Approval Enforcement:**
  When evaluating booking requests, the backend compares `requester_email` with the authenticated JWT subject. If matching, approvals are rejected at the service layer with HTTP 403.
- **Strict Solver Authority:**
  All natural language, conversational, or manual user requests pass through [`candidates.py`](file:///d:/TTMS/backend/app/scheduler/candidates.py) and [`hard.py`](file:///d:/TTMS/backend/app/validators/hard.py) before reaching the database.
- **Audit Logging:**
  Administrative actions (overrides, disruptions, settings changes) are permanently written to the audit log collection.
