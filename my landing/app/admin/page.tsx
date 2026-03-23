import { listLeads } from "@/lib/db/repository";
import { isAdminAuthorized } from "@/lib/admin-auth";

const tableCell: React.CSSProperties = {
  padding: "14px 16px",
  borderBottom: "1px solid rgba(148,255,197,0.14)",
  verticalAlign: "top",
  color: "rgba(239,255,245,0.85)",
};

export default async function AdminPage() {
  const allowed = await isAdminAuthorized();

  if (!allowed) {
    return (
      <main
        style={{
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "linear-gradient(180deg, #03110b 0%, #071914 100%)",
          color: "#effff5",
          fontFamily: "var(--font-body), sans-serif",
          padding: 24,
        }}
      >
        <div
          style={{
            width: "min(100%, 520px)",
            padding: 28,
            border: "1px solid rgba(148,255,197,0.16)",
            background: "rgba(9, 26, 19, 0.88)",
          }}
        >
          <p style={{ margin: "0 0 12px", letterSpacing: "0.18em", textTransform: "uppercase", color: "#99ffc0" }}>
            Admin
          </p>
          <h1 style={{ margin: 0, fontFamily: "var(--font-display), serif", fontSize: "clamp(2rem, 7vw, 3.2rem)" }}>
            Нужна Basic Auth авторизация
          </h1>
          <p style={{ color: "rgba(239,255,245,0.72)", lineHeight: 1.7 }}>
            Открой страницу с логином и паролем из `.env.local` или поменяй их на свои значения.
          </p>
        </div>
      </main>
    );
  }

  const leads = await listLeads();

  return (
    <main
      style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #03110b 0%, #071914 100%)",
        color: "#effff5",
        fontFamily: "var(--font-body), sans-serif",
        padding: 24,
      }}
    >
      <div style={{ width: "min(100%, 1280px)", margin: "0 auto" }}>
        <p style={{ margin: "0 0 10px", letterSpacing: "0.18em", textTransform: "uppercase", color: "#99ffc0" }}>
          Admin / leads
        </p>
        <h1 style={{ margin: 0, fontFamily: "var(--font-display), serif", fontSize: "clamp(2.2rem, 6vw, 4rem)" }}>
          Входящие заявки
        </h1>
        <p style={{ color: "rgba(239,255,245,0.72)", lineHeight: 1.7 }}>
          Отдельный контур для просмотра лидов. Дальше можно будет добавить фильтры, статусы и ручную обработку.
        </p>

        <div
          style={{
            marginTop: 24,
            border: "1px solid rgba(148,255,197,0.16)",
            background: "rgba(9, 26, 19, 0.88)",
            overflowX: "auto",
          }}
        >
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 980 }}>
            <thead>
              <tr style={{ textAlign: "left", color: "#99ffc0" }}>
                <th style={tableCell}>Дата</th>
                <th style={tableCell}>Имя</th>
                <th style={tableCell}>Компания</th>
                <th style={tableCell}>Контакт</th>
                <th style={tableCell}>Бюджет</th>
                <th style={tableCell}>Задача</th>
              </tr>
            </thead>
            <tbody>
              {leads.map((lead) => (
                <tr key={lead.id}>
                  <td style={tableCell}>{lead.createdAt}</td>
                  <td style={tableCell}>{lead.name}</td>
                  <td style={tableCell}>{lead.company}</td>
                  <td style={tableCell}>{lead.telegramOrEmail}</td>
                  <td style={tableCell}>{lead.budgetRange}</td>
                  <td style={{ ...tableCell, minWidth: 340 }}>{lead.projectSummary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
