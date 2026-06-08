function DashboardPage() {
  return (
    <section>
      <h2>Dashboard</h2>

      <div className="dashboard-grid">
        <div className="card">
          <h3>Total Students</h3>
          <p>0</p>
        </div>

        <div className="card">
          <h3>Total Counselors</h3>
          <p>0</p>
        </div>

        <div className="card">
          <h3>Appointments Planned</h3>
          <p>0</p>
        </div>

        {/* <div className="card">
          <h3>Missing Documents</h3>
          <p>0</p>
        </div> */}
      </div>

      <div className="card">
        <h3> Workflow</h3>
        <ol>
          <li>Import students</li>
          <li>Add counselors</li>
          <li>Create time slots</li>
          <li>Plan counseling appointments</li>
          <li>Send student and counselor emails</li>
          <li>Track documents and minutes</li>
          <li>Prepare final bundle</li>
        </ol>
      </div>
    </section>
  );
}

export default DashboardPage;
