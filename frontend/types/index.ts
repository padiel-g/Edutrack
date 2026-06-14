export type Role = "Super Admin" | "Admin" | "Teacher" | "Student" | "Parent" | "Accounts Officer";

export type User = {
  id: number;
  email: string;
  name: string;
  firstName: string;
  lastName: string;
  role: Role;
  permissions: string[];
  status?: "Active" | "Inactive" | "Suspended";
  mustChangePassword?: boolean;
  lastLoginAt?: string | null;
  passwordChangedAt?: string | null;
};
