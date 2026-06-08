function StudentImportPage() {
  return (
    <section>
      <h2>Import Students</h2>

      <div className="card">
        <p>
          {/* Paste or upload student data from the study office. Later, the admin
          can map columns to matriculation number, name, email, course,
          semester, and credit points. */}
        </p>

        <label>Paste Excel Data</label>
        <textarea rows={10} placeholder="Paste Excel data here..." />

        <button>Preview</button>
        <button>Import Students</button>
      </div>
    </section>
  );
}

export default StudentImportPage;
