import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import DashboardPage from "./pages/DashboardPage";
import StudentImportPage from "./pages/StudentImportPage";
import StudentsPage from "./pages/StudentsPage";
import CounselorsPage from "./pages/CounselorsPage";
import SlotsPage from "./pages/SlotsPage";
import StudentMailPage from "./pages/StudentMailPage";
import CounselorMailPage from "./pages/CounselorMailPage";
import AppointmentsPage from "./pages/AppointmentPage";
import TemplatesPage from "./pages/TemplatesPage";
import MailPage from "./pages/MailPage";
// ...inside <Routes><Route path="/" element={<AppLayout />}>...

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="students/import" element={<StudentImportPage />} />
          <Route path="students" element={<StudentsPage />} />
          <Route
            path="students/:studentId/mail"
            element={<StudentMailPage />}
          />
          <Route path="counselors" element={<CounselorsPage />} />
          <Route
            path="counselors/:counselorId/mail"
            element={<CounselorMailPage />}
          />
          <Route path="templates" element={<TemplatesPage />} />
          <Route path="mail" element={<MailPage />} />
          <Route path="slots" element={<SlotsPage />} />
          <Route path="appointments" element={<AppointmentsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
