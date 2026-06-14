import { BarChart3, Bell, BookOpen, CalendarDays, ClipboardCheck, CreditCard, FileText, GraduationCap, Home, Megaphone, MessageSquare, Settings, Shield, Users } from "lucide-react";
import type { ComponentType } from "react";
import type { Role } from "@/types";

export const navByRole: Record<Role, { href: string; label: string; icon: ComponentType<{ className?: string }> }[]> = {
  "Super Admin": [],
  Admin: [
    { href: "/admin", label: "Dashboard", icon: Home },
    { href: "/admin/students", label: "Students", icon: GraduationCap },
    { href: "/admin/teachers", label: "Teachers", icon: Users },
    { href: "/admin/accounts", label: "Accounts", icon: CreditCard },
    { href: "/admin/fees-overview", label: "Fees Overview", icon: BarChart3 },
    { href: "/admin/parents", label: "Parents", icon: Users },
    { href: "/admin/classes", label: "Classes", icon: BookOpen },
    { href: "/admin/subjects", label: "Subjects", icon: BookOpen },
    { href: "/admin/academic-years", label: "Academic Years", icon: CalendarDays },
    { href: "/admin/terms", label: "Terms", icon: CalendarDays },
    { href: "/admin/timetable", label: "Timetable", icon: CalendarDays },
    { href: "/admin/registers", label: "Registers", icon: ClipboardCheck },
    { href: "/admin/announcements", label: "Announcements", icon: Megaphone },
    { href: "/admin/reports", label: "Report Cards", icon: FileText },
    { href: "/admin/users-and-roles", label: "Users & Roles", icon: Shield },
    { href: "/admin/audit-logs", label: "Audit Logs", icon: ClipboardCheck },
    { href: "/admin/settings", label: "Settings", icon: Settings }
  ],
  Teacher: [
    { href: "/teacher", label: "Dashboard", icon: Home },
    { href: "/teacher/my-classes", label: "My Classes", icon: Users },
    { href: "/teacher/my-subjects", label: "My Subjects", icon: BookOpen },
    { href: "/teacher/timetable", label: "Timetables", icon: CalendarDays },
    { href: "/teacher/attendance", label: "Attendance", icon: ClipboardCheck },
    { href: "/teacher/results-upload", label: "Results Upload", icon: BarChart3 },
    { href: "/teacher/continuous-assessment", label: "Assessment", icon: FileText },
    { href: "/teacher/assignments", label: "Assignments", icon: FileText },
    { href: "/teacher/submissions", label: "Submissions", icon: ClipboardCheck },
    { href: "/teacher/learning-materials", label: "Materials", icon: BookOpen },
    { href: "/teacher/announcements", label: "Announcements", icon: Megaphone },
    { href: "/teacher/class-performance", label: "Performance", icon: BarChart3 },
    { href: "/teacher/teacher-comments", label: "Complete Reports", icon: MessageSquare }
  ],
  Student: [
    { href: "/student", label: "Dashboard", icon: Home },
    { href: "/student/my-results", label: "My Results", icon: BarChart3 },
    { href: "/student/my-attendance", label: "Attendance", icon: ClipboardCheck },
    { href: "/student/my-assignments", label: "Assignments", icon: FileText },
    { href: "/student/learning-materials", label: "Materials", icon: BookOpen },
    { href: "/student/timetable", label: "Timetable", icon: CalendarDays },
    { href: "/student/fee-balance", label: "Fee Balance", icon: CreditCard },
    { href: "/student/announcements", label: "Announcements", icon: Megaphone },
  ],
  Parent: [
    { href: "/parent", label: "Dashboard", icon: Home },
    { href: "/parent/my-children", label: "My Children", icon: Users },
    { href: "/parent/learning-materials", label: "Learning Materials", icon: BookOpen },
    { href: "/parent/child-results", label: "Results", icon: BarChart3 },
    { href: "/parent/child-attendance", label: "Attendance", icon: ClipboardCheck },
    { href: "/parent/timetable", label: "Timetables", icon: CalendarDays },
    { href: "/parent/child-fees", label: "Fees", icon: CreditCard },
    { href: "/parent/payment-history", label: "Payments", icon: CreditCard },
    { href: "/parent/report-cards", label: "Report Cards", icon: FileText },
    { href: "/parent/teacher-comments", label: "Comments", icon: MessageSquare },
    { href: "/parent/announcements", label: "Announcements", icon: Megaphone },
    { href: "/parent/notifications", label: "Notifications", icon: Bell },
    { href: "/parent/change-password", label: "Change Password", icon: Settings }
  ],
  "Accounts Officer": [
    { href: "/accounts", label: "Dashboard", icon: Home },
    { href: "/accounts/student-fee-accounts", label: "Student Fee Accounts", icon: Users },
    { href: "/accounts/invoices", label: "Invoices", icon: FileText },
    { href: "/accounts/payments", label: "Payments", icon: CreditCard },
    { href: "/accounts/record-payment", label: "Record Payment", icon: CreditCard },
    { href: "/accounts/paid-students", label: "Paid Students", icon: Users },
    { href: "/accounts/unpaid-students", label: "Unpaid Students", icon: Users },
    { href: "/accounts/overdue-balances", label: "Overdue Balances", icon: CreditCard },
    { href: "/accounts/fee-reminders", label: "Fee Reminders", icon: Bell },
    { href: "/accounts/finance-reports", label: "Finance Reports", icon: BarChart3 },
    { href: "/accounts/change-password", label: "Change Password", icon: Settings },
    { href: "/accounts/settings", label: "Settings", icon: Settings }
  ]
};

navByRole["Super Admin"] = navByRole.Admin;
