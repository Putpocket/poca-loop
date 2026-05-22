import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppLayout } from "../components/app-layout";
import { AdminPendingPhotocardsPage } from "../pages/admin-pending-photocards";
import { DashboardPage } from "../pages/dashboard";
import { DirectMatchesPage } from "../pages/direct-matches";
import { ExplorePage } from "../pages/explore";
import { HavesPage } from "../pages/haves";
import { LoginPage } from "../pages/login";
import { SignupPage } from "../pages/signup";
import { ThreeWayMatchesPage } from "../pages/three-way-matches";
import { WantsPage } from "../pages/wants";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/signup", element: <SignupPage /> },
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "explore", element: <ExplorePage /> },
      { path: "haves", element: <HavesPage /> },
      { path: "wants", element: <WantsPage /> },
      { path: "matches/direct", element: <DirectMatchesPage /> },
      { path: "matches/three-way", element: <ThreeWayMatchesPage /> },
      { path: "admin/pending-photocards", element: <AdminPendingPhotocardsPage /> }
    ]
  },
  { path: "*", element: <Navigate to="/dashboard" replace /> }
]);
