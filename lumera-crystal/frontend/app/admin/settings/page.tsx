import { AdminPageShell } from "@/components/admin/page-shell";

export default function AdminSettingsPage() {
  return (
    <AdminPageShell title="设置" description="预留品牌与系统配置入口。">
      <div className="rounded-2xl border border-dashed border-stone-300 bg-white/60 p-10 text-center text-sm text-stone-500">
        设置模块占位。后续可扩展管理员信息、对象存储、邮件通知、AI 助手配置。
      </div>
    </AdminPageShell>
  );
}
