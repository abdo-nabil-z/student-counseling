// import { useEffect, useState } from "react";

// type Appointment = {
//   id: number;
//   studentName: string;
//   matriculationNumber: string;
//   studyProgram: string;
//   date: string;
//   time: string;
//   studyPlanStatus: "Uploaded" | "Missing";
//   transcriptStatus: "Uploaded" | "Missing";
//   minutesStatus: "Not uploaded" | "Uploaded";
// };

// const appointments: Appointment[] = [
//   {
//     id: 1,
//     studentName: "Max Müller",
//     matriculationNumber: "123456",
//     studyProgram: "Computer Science",
//     date: "15.10.2026",
//     time: "10:00 - 10:30",
//     studyPlanStatus: "Uploaded",
//     transcriptStatus: "Uploaded",
//     minutesStatus: "Not uploaded",
//   },
//   {
//     id: 2,
//     studentName: "Anna Weber",
//     matriculationNumber: "654321",
//     studyProgram: "Information Systems",
//     date: "15.10.2026",
//     time: "10:30 - 11:00",
//     studyPlanStatus: "Missing",
//     transcriptStatus: "Missing",
//     minutesStatus: "Not uploaded",
//   },
// ];

// function CounselorDashboard() {
//   const [echoData, setEchoData] = useState<string | null>(null);
//   const [echoError, setEchoError] = useState<string | null>(null);

//   useEffect(() => {
//     fetch("/api/counselors/echo-data/")
//       .then((res) => res.json())
//       .then((data) => setEchoData(JSON.stringify(data)))
//       .catch((err) => setEchoError(String(err)));
//   }, []);

//   return (
//     <main>
//       <h1>Counselor Dashboard</h1>
//       <p>Here you can see your assigned counseling appointments.</p>

//       <p>
//         <strong>Backend connection check:</strong>{" "}
//         {echoError
//           ? `Error: ${echoError}`
//           : echoData !== null
//             ? echoData
//             : "Loading…"}
//       </p>

//       <table border={1} cellPadding={8}>
//         <thead>
//           <tr>
//             <th>Student</th>
//             <th>Study Program</th>
//             <th>Date</th>
//             <th>Time</th>
//             <th>Study Plan</th>
//             <th>Transcript</th>
//             <th>Minutes</th>
//           </tr>
//         </thead>

//         <tbody>
//           {appointments.map((appointment) => (
//             <tr key={appointment.id}>
//               <td>{appointment.studentName}</td>
//               <td>{appointment.studyProgram}</td>
//               <td>{appointment.date}</td>
//               <td>{appointment.time}</td>
//               <td>{appointment.studyPlanStatus}</td>
//               <td>{appointment.transcriptStatus}</td>
//               <td>{appointment.minutesStatus}</td>
//             </tr>
//           ))}
//         </tbody>
//       </table>
//     </main>
//   );
// }

// function App() {
//   return <CounselorDashboard />;
// }

// export default App;
import { BrowserRouter, Routes, Route } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import DashboardPage from "./pages/DashboardPage";

import StudentImportPage from "./pages/StudentImportPage";
import StudentsPage from "./pages/StudentsPage";
import CounselorsPage from "./pages/CounselorsPage";
import SlotsPage from "./pages/SlotsPage";
// import PlanningPage from "./pages/PlanningPage";
import StudentMailPage from "./pages/StudentMailPage";
import CounselorMailPage from "./pages/CounselorMailPage";
// import DocumentsPage from "./pages/DocumentsPage";
// import MinutesPage from "./pages/MinutesPage";
// import NoShowPage from "./pages/NoShowPage";
// import FinalBundlePage from "./pages/FinalBundlePage";
import AppointmentsPage from "./pages/ApointmentsPage"; // remove PlanningPage + SessionsPage imports

import "./App.css";
import SessionsPage from "./pages/sessionspage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          {
            <>
              <Route index element={<DashboardPage />} />
              <Route path="students/import" element={<StudentImportPage />} />
              <Route path="students" element={<StudentsPage />} />
              <Route
                path="students/:studentId/mail"
                element={<StudentMailPage />}
              />
              <Route
                path="counselors/:counselorId/mail"
                element={<CounselorMailPage />}
              />
              <Route path="counselors" element={<CounselorsPage />} />
              <Route path="slots" element={<SlotsPage />} />
              <Route path="documents" element={<SessionsPage />} />
              {/* <Route path="planning" element={<PlanningPage />} /> */}
              // remove these two:
              <Route path="appointments" element={<AppointmentsPage />} />
              {/* <Route path="student-mail" element={<StudentMailPage />} /> */}
              {/* <Route path="counselor-mail" element={<CounselorMailPage />} /> */}
            </>
            /*<Route path="documents" element={<DocumentsPage />} />
          <Route path="minutes" element={<MinutesPage />} />
          <Route path="no-shows" element={<NoShowPage />} />
          <Route path="final-bundle" element={<FinalBundlePage />} /> */
          }
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
