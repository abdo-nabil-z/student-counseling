import { useEffect, useState } from "react";
import api from "../api/client";

interface MailSettings {
  smtp_host: string;
  smtp_port: number;
  use_tls: boolean;
  smtp_username: string;
  from_name: string;
  from_email: string;
  persist_credentials: boolean;
  password_configured: boolean;
}

const DEFAULT_SETTINGS: MailSettings = {
  smtp_host: "email.uni-rostock.de",
  smtp_port: 587,
  use_tls: true,
  smtp_username: "",
  from_name: "",
  from_email: "",
  persist_credentials: false,
  password_configured: false,
};

function getSettingsError(error: unknown, fallback: string): string {
  const apiError = (
    error as {
      response?: {
        data?: {
          error?: {
            message?: string;
            details?: unknown;
          };
        };
      };
    }
  ).response?.data?.error;

  if (!apiError) return fallback;

  const details = apiError.details ? JSON.stringify(apiError.details) : "";

  return [apiError.message, details].filter(Boolean).join(" ");
}

function MailSettingsPage() {
  const [settings, setSettings] = useState<MailSettings>(DEFAULT_SETTINGS);

  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<MailSettings>("/mailing/settings/")
      .then((response) => setSettings(response.data))
      .catch((requestError: unknown) =>
        setError(
          getSettingsError(requestError, "Could not load mail settings."),
        ),
      )
      .finally(() => setLoading(false));
  }, []);

  function updateSetting<K extends keyof MailSettings>(
    key: K,
    value: MailSettings[K],
  ) {
    setSettings((current) => ({
      ...current,
      [key]: value,
    }));
  }

  async function saveSettings() {
    setSaving(true);
    setMessage(null);
    setError(null);

    try {
      const response = await api.put<MailSettings>("/mailing/settings/", {
        smtp_host: settings.smtp_host,
        smtp_port: settings.smtp_port,
        use_tls: settings.use_tls,
        smtp_username: settings.smtp_username,
        password,
        from_name: settings.from_name,
        from_email: settings.from_email,
        persist_credentials: settings.persist_credentials,
      });

      setSettings(response.data);
      setPassword("");
      setMessage("Mail settings saved.");
    } catch (requestError: unknown) {
      setError(getSettingsError(requestError, "Could not save mail settings."));
    } finally {
      setSaving(false);
    }
  }

  async function testConnection() {
    setTesting(true);
    setMessage(null);
    setError(null);

    try {
      await api.post("/mailing/settings/test/");
      setMessage("Connection successful.");
    } catch (requestError: unknown) {
      setError(
        getSettingsError(requestError, "Could not connect to the mail server."),
      );
    } finally {
      setTesting(false);
    }
  }

  async function clearSettings() {
    if (!window.confirm("Clear the saved mail credentials?")) {
      return;
    }

    setMessage(null);
    setError(null);

    try {
      await api.delete("/mailing/settings/");
      setSettings(DEFAULT_SETTINGS);
      setPassword("");
      setMessage("Mail credentials cleared.");
    } catch (requestError: unknown) {
      setError(
        getSettingsError(requestError, "Could not clear mail settings."),
      );
    }
  }

  return (
    <section>
      <h2>Mail settings</h2>

      <p>Configure the account used to send email.</p>

      {loading && <p>Loading mail settings…</p>}
      {error && <p className="error-text">{error}</p>}
      {message && <p>{message}</p>}

      {!loading && (
        <div className="card">
          <label htmlFor="smtp-host">SMTP host</label>
          <input
            id="smtp-host"
            value={settings.smtp_host}
            onChange={(event) => updateSetting("smtp_host", event.target.value)}
          />

          <label htmlFor="smtp-port">SMTP port</label>
          <input
            id="smtp-port"
            type="number"
            min={1}
            max={65535}
            step={1}
            value={settings.smtp_port}
            onChange={(event) => {
              const value = event.target.value;

              if (
                /^\d+$/.test(value) &&
                Number(value) >= 1 &&
                Number(value) <= 65535
              ) {
                updateSetting("smtp_port", Number(value));
              }
            }}
          />

          <label htmlFor="smtp-username">Username</label>
          <input
            id="smtp-username"
            value={settings.smtp_username}
            onChange={(event) =>
              updateSetting("smtp_username", event.target.value)
            }
          />

          <label htmlFor="smtp-password">Password</label>
          <input
            id="smtp-password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder={
              settings.password_configured
                ? "Leave blank to keep the saved password"
                : "Enter the email password"
            }
          />

          <label htmlFor="from-name">Sender name</label>
          <input
            id="from-name"
            value={settings.from_name}
            onChange={(event) => updateSetting("from_name", event.target.value)}
          />

          <label htmlFor="from-email">Sender email</label>
          <input
            id="from-email"
            type="email"
            value={settings.from_email}
            onChange={(event) =>
              updateSetting("from_email", event.target.value)
            }
          />

          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <input
              type="checkbox"
              checked={settings.use_tls}
              onChange={(event) =>
                updateSetting("use_tls", event.target.checked)
              }
            />
            Use TLS
          </label>

          <label
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
            }}
          >
            <input
              type="checkbox"
              checked={settings.persist_credentials}
              onChange={(event) =>
                updateSetting("persist_credentials", event.target.checked)
              }
            />
            Remember credentials after the server restarts
          </label>

          <div style={{ marginTop: "1rem" }}>
            <button type="button" onClick={saveSettings} disabled={saving}>
              {saving ? "Saving…" : "Save settings"}
            </button>

            <button type="button" onClick={testConnection} disabled={testing}>
              {testing ? "Testing…" : "Test saved connection"}
            </button>

            <button type="button" onClick={clearSettings}>
              Clear credentials
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

export default MailSettingsPage;
