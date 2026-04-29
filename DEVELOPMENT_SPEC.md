# Technical Specification & Implementation Blueprint: "Dima Chat" SPA

## 1. Project Overview
The "Dima Chat" project is a Single File Application (SFA) designed to provide an interactive, persona-driven chat experience. The core value proposition is the dynamic visual feedback of the character "Dima," whose facial expressions change in real-time based on the temporal distance from the last interaction ($\Delta T$) and the semantic content of the conversation.

The application must be entirely self-contained within a single `.html` file, requiring no external network requests for logic, styling, or assets (once assets are embedded as Base64).

---

## 2. System Architecture: Single File Autonomy
### 2.1 The SFA Paradigm
Since the application runs locally without a backend, all "intelligence" must reside in the client-side JavaScript engine. This eliminates the need for an API but shifts the responsibility of data parsing and state management entirely to the browser's runtime.

### 2.2 Component Breakdown
1.  **HTML5 Layer**: Defines the structural skeleton (Chat Container, Avatar Viewport, Message Feed, Input Area).
2.  **CSS3 Layer (The Visual Engine)**: Handles layout via Flexbox/Grid, defines "Chat Bubble" aesthetics, and implements smooth transitions for avatar opacity/scaling to prevent jarring visual jumps during emotion switches.
3.  **JavaScript Layer (The Brain)**:
    *   **Data Store**: A static object containing the parsed replies and Base64 image strings.
    *   **State Machine**: Manets the current $\text{EmotionState}$ and $\Delta T$.
    *   **Event Loop**: Monitors user input and a high-frequency timer for $\Delta.T$ monitoring.
    *   **Typewriter Engine**: Controls the text rendering speed.

---

## 3. Detailed Functional Requirements

### 3.1 The Avatar State Machine (ASM)
The most critical component is the transition logic between visual states. We define three primary logical layers:

#### A. The Temporal Layer (Idle Logic)
This layer operates on a continuous clock.
*   **Variable**: $\Delta T = \text{CurrentTime} - \text{LastEventTimestamp}$
*   **Condition 1 ($\Delta T < 5\text{s}$)**: The system is in "Active Waiting" mode. The avatar must display `avatar_1.jpeg` (Neutral).
*   **Condition 2 ($\Delta T \ge 5\text{s}$)**: The system enters "Long Idle" mode. The avatar must display `avatar_8.jpeg` (Tired).

#### B. The Semantic Layer (Active Dialogue)
Triggered whenever a new message is processed from the mapping file.
*   **Trigger**: User sends a message $\to$ System selects a reply $R_i$.
*   **Logic**: If index $i \notin \{1, 8\}$, the system bypasss the temporal layer and forces the avatar specified in the `replies_mapping.md` (e.g., `avatar_3.jpeg` for "Attentive").

#### C. The Reset/Interrupt Trigger
Every user interaction resets the $\Delta T$ clock to zero, momentarily forcing the state back to "Neutral" or "Active" before the timer can drift into "Tired" territory.

### 3.2 The Typewriter Engine (Textual Animation)
To simulate human-like typing, the response must not appear instantaneously.
*   **Target Velocity**: $5 \text{ characters per second}$.
*   **Implementation**: 
    *   A recursive `setTimeout` or a `setInterval` loop.
    *   Each iteration takes one character from the selected string and appends it to the DOM.
    *   The delay between characters should be exactly $200\text{ms}$ ($1000\text{ms} / 5 \text{ chars}$).

### 3.3 The Reply Selection Engine (Randomization)
*   **Source**: `replies_mapping.md`.
*   **Algorithm**: 
    1.  Load all lines from the mapping array.
    2.  Generate a random integer $k$ where $0 \le k < \text{ArrayLength}$.
    3.  Retrieve $R_k$.
    *   If $k=1$ or $k=8$, trigger "Idle Mode" logic.
    *   Otherwise, trigger "Active Mode" logic.

---

## 4. Technical Implementation Roadmap

### Phase 1: Data Extraction & Preparation (The Pipeline)
Before writing the HTML, the developer must perform two preprocessing steps:

**Step 1: Mapping Conversion**
Convert the Markdown table from `@replies_mapping.md` into a JSON-compatible JavaScript array within the script tag:
```javascript
const DI_REPLIES = [
  { id: 1, text: "...", avatar: "avatar_2.jpeg", emotion: "Задумчивый (Idle)" },
  // ... etc
];
```

**Step 2: Asset Encoding (The Base64 Step)**
Since the app must be a single file, the images in `avatars/split/` must be converted to Data URIs.
*   **Command**: `base64 image_path`
*   **Integration**: Create a constant `const ASSETS = { avatar_1: "data:image/jpeg;base64,/9j/4AAQ..." };`

### Phase 2: HTML/CSS Construction
The UI must be robust and responsive.
*   **Container**: A centered `max-width: 600px` div.
*   **Avatar Wrapper**: A fixed-size square container with `overflow: hidden`.
*   **Message Feed**: An `overflow-y: auto` region that auto-scrolls to the bottom on every new message.

### Phase 3: JavaScript Core Development
The developer must implement the following functions:
1.  `handleUserMessage(text)`: The entry point for user input.
2.  `processDimaReply()`: The function that selects a random reply and starts the typewriter.
3.  `updateAvatar(avatarPath)`: A function to swap `img.src` with a CSS opacity transition.
4.  `startHeartbeat()`: A `setInterval` running every $100\text{ms}$ to monitor $\Delta T$.

---

## 5. Error Handling & Edge Cases
*   **Missing Asset**: If a selected avatar index is not found in the `ASSETS` object, fallback to `avatar_2.jpeg` (Задумчивый).
*   **Empty Input**: Ignore empty user messages to prevent unnecessary $\Delta T$ resets.
*   **Rapid-fire Messages**: If a user sends messages faster than $200\text{ms}$, the typewriter engine must clear the existing buffer and restart to avoid text overlapping or "glitching".

---

## 6. Summary of Rules for Implementation
| Feature | Rule |
| :--- | :--- |
| **Avatar Transition** | Must use CSS `transition` for smoothness. |
| **$\Delta T$ Threshold** | Exactly $5.0$ seconds. |
| **Typing Speed** | Fixed at $200\text{ms}$ per character. |
| **File Structure** | Strictly 1 file: `index.html`. |
| **Data Source** | Hardcoded into the script via pre-parsed MD and Base64. |
