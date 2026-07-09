import { useEffect, useState } from "react";
import api from "../api/client";

function DashboardPage() {
  const [counts, setCounts] = useState({
    students: 0,
    counselors: 0,
    appointments: 0,
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get("/students/"),
      api.get("/counselors/"),
      api.get("/appointments/"),
    ])
      .then(([s, c, a]) =>
        setCounts({
          students: s.data.length,
          counselors: c.data.length,
          appointments: a.data.length,
        }),
      )
      .catch((e) => setError(e.message));
  }, []);

  return (
    <section>
      <h2>Dashboard</h2>
      {error && <p style={{ color: "red" }}>Backend error: {error}</p>}
      <div className="dashboard-grid">
        <div className="card">
          <h3>Total Students</h3>
          <p>{counts.students}</p>
        </div>
        <div className="card">
          <h3>Total Counselors</h3>
          <p>{counts.counselors}</p>
        </div>
        <div className="card">
          <h3>Appointments Planned</h3>
          <p>{counts.appointments}</p>
        </div>
      </div>
    </section>
  );
}

export default DashboardPage;
