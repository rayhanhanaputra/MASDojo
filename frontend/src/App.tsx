import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { DashboardPage } from "./pages/DashboardPage";
import { TaskPage } from "./pages/TaskPage";
import { SettingsPage } from "./pages/SettingsPage";
import { ProfilePage } from "./pages/ProfilePage";
import { VerifyPage } from "./pages/VerifyPage";
import { Spinner, Wordmark } from "./components/ui";
import type { ReactNode } from "react";

function Protected({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="grid h-full place-items-center px-5">
        <div className="flex flex-col items-center gap-4 animate-rise">
          <Wordmark size="lg" />
          <Spinner label="booting dojo…" />
        </div>
      </div>
    );
  }
  return user ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  const { soloMode } = useAuth();
  return (
    <Routes>
      {/* Solo mode has no accounts — send auth routes into the curriculum. */}
      <Route path="/login" element={soloMode ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route
        path="/register"
        element={soloMode ? <Navigate to="/" replace /> : <RegisterPage />}
      />
      <Route path="/verify" element={<VerifyPage />} />
      <Route
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route path="/" element={<DashboardPage />} />
        <Route path="/tasks/:taskId" element={<TaskPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
