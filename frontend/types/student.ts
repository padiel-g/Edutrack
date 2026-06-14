export type StudentSubject = {
  id: number;
  code: string;
  name: string;
  stream?: string | null;
};

export type Student = {
  id: number;
  registrationNumber: string;
  firstName: string;
  middleName?: string;
  lastName: string;
  name: string;
  gender?: string;
  dateOfBirth?: string;
  birthCertificateNumber?: string;
  nationalId?: string;
  classId?: number;
  class?: string;
  classType?: string;
  academicYearId?: number;
  parentId?: number;
  address?: string;
  phone?: string;
  email?: string;
  enrollmentDate?: string;
  status: string;
  gradeForm?: string | null;
  classStream?: string | null;
  numberOfSubjects?: number | null;
  subjects?: StudentSubject[];
};
