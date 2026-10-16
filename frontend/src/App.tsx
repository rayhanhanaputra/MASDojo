import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { DashboardPage } from "./pages/DashboardPage";
import { TaskPage } from "./pages/TaskPage";
import { SettingsPage } from "./pages/SettingsPage";
import { ProfilePage } from "./pages/ProfilePage";
import { AdminPage } from "./pages/AdminPage";
import { InstructorPage } from "./pages/InstructorPage";
import { StudentsPage } from "./pages/StudentsPage";
import { Spinner, Wordmark } from "./components/ui";
import type { ReactNode } from "react";

const ROLE_RANK = { learner: 0, instructor: 1, admin: 2 } as const;

function RequireRole({ min, children }: { min: "instructor" | "admin"; children: ReactNode }) {
  const { user } = useAuth();
  const rank = user ? ROLE_RANK[user.role] ?? 0 : 0;
  return rank >= ROLE_RANK[min] ? <>{children}</> : <Navigate to="/" replace />;
}

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
        <Route
          path="/instructor"
          element={
            <RequireRole min="instructor">
              <InstructorPage />
            </RequireRole>
          }
        />
        <Route
          path="/students"
          element={
            <RequireRole min="instructor">
              <StudentsPage />
            </RequireRole>
          }
        />
        <Route
          path="/admin"
          element={
            <RequireRole min="admin">
              <AdminPage />
            </RequireRole>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
