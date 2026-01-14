# Learn Loop - Frontend Client

This is the React + TypeScript frontend for **Learn Loop**, built with Vite and Tailwind CSS.

## 🚀 Key Features
- **Kid-Friendly UI**: Large tactile buttons, high-contrast colors, and bouncy animations.
- **Progress Visualization**: A "Knowledge Tree" that grows in real-time as the child's understanding improves (powered by Framer Motion).
- **Dual-Mode Input**: Supports both Text and Voice (OpenAI Whisper integration).
- **Professional State Management**: Redux Toolkit for complex session tracking.
- **Fast Data Fetching**: React Query for efficient API synchronization.

## 🛠️ Tech Stack
- **Build Tool**: Vite
- **UI Logic**: React + TypeScript
- **State**: Redux Toolkit
- **Styling**: Tailwind CSS
- **Animations**: Framer Motion
- **Icons**: Lucide React

## 🏃 Getting Started

1.  **Install dependencies**:
    ```bash
    npm install
    ```

2.  **Run development server**:
    ```bash
    npm run dev
    ```

3.  **Build for production**:
    ```bash
    npm run build
    ```

## 📂 Folder Structure
- `src/app`: Global providers and configuration.
- `src/features`: Feature-based logic (Learning, Parent Dashboard).
- `src/components/ui`: Reusable UI components.
- `src/services`: API client and services.
- `src/hooks`: Custom React hooks (including typed Redux hooks).
- `src/store`: Redux store configuration.
