// ==================== Base Types ====================
export interface BaseModel {
  id: string;
  createdAt: string;
  updatedAt: string;
}

export type Currency = 'BDT' | 'USD' | 'EUR' | 'GBP' | 'INR' | 'SGD' | 'SAR';

// ==================== User / Auth ====================
export interface User {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  currency: string;
  dateFormat: string;
  darkMode: boolean;
  notifications: NotificationPreference;
}

export interface NotificationPreference {
  email: boolean;
  push: boolean;
  budgetAlert: boolean;
  lowBalance: boolean;
  loanReminder: boolean;
}

// ==================== Income Category ====================
// NOTE: Income categories are separate from Expense categories.
// Income uses IncomeCategory, Expense uses ExpenseCategory.
// Transaction.categoryId can reference either depending on Transaction.type.
export interface IncomeCategory extends BaseModel {
  name: string;
  icon: string;
  color: string;
  type: 'salary' | 'freelance' | 'business' | 'investment' | 'rental' | 'refund' | 'gift' | 'other';
}

// ==================== Bank Account & Transaction ====================
// NOTE: Transaction is the bank-level ledger (raw what-hits-your-account record).
// Income and Expense are categorized detail records that link to transactions.
// Relationship: Transaction (1) ←→ (0..1) Income or Expense
//   - Each Income/Expense record optionally links to a Transaction via transactionId
//   - Not all transactions have Income/Expense records (e.g., transfers)
//   - Not all Income/Expense records have transactions (e.g., pending receivables)
export interface BankAccount extends BaseModel {
  bankName: string;
  accountNumber: string;
  accountName: string;
  type: 'savings' | 'checking' | 'current' | 'fixed_deposit' | 'salary';
  openingBalance: number;
  icon?: string;
  color?: string;
  currency?: Currency;
  isActive: boolean;
}

export interface Transaction extends BaseModel {
  type: 'income' | 'expense' | 'transfer';
  amount: number;
  direction: 'credit' | 'debit';
  bankAccountId: string;
  toBankAccountId?: string;
  categoryId: string;
  date: string;
  description: string;
  referenceId?: string;
  tags?: string[];
  currency?: Currency;
}

// ==================== Income ====================
export interface Income extends BaseModel {
  sourceId: string;
  amount: number;
  date: string;
  bankAccountId: string;
  categoryId: string;             // References IncomeCategory (NOT ExpenseCategory)
  transactionId?: string;          // Links to bank Transaction record
  description: string;
  isRecurring: boolean;
  recurringCycle?: 'daily' | 'weekly' | 'monthly' | 'yearly';
  currency?: Currency;
}

export interface IncomeSource extends BaseModel {
  name: string;
  type: 'salary' | 'freelance' | 'business' | 'investment' | 'rental' | 'other';
  isActive: boolean;
  monthlyAmount?: number;
}

// ==================== Expense ====================
export interface Expense extends BaseModel {
  amount: number;
  date: string;
  bankAccountId?: string;
  cardId?: string;
  categoryId: string;             // References ExpenseCategory
  transactionId?: string;          // Links to bank Transaction record
  description: string;
  isRecurring: boolean;
  recurringCycle?: 'daily' | 'weekly' | 'monthly' | 'yearly';
  tags?: string[];
  currency?: Currency;
}

export interface ExpenseCategory extends BaseModel {
  name: string;
  icon: string;
  color: string;
  type: 'needs' | 'wants' | 'savings' | 'investments';
  budgetLimit?: number;
  currency?: Currency;
}

// ==================== Cards ====================
export interface Card extends BaseModel {
  bankAccountId: string;
  name: string;
  type: 'debit' | 'credit';
  cardNumber: string;
  holderName: string;
  expiryDate: string;
  brand: 'visa' | 'mastercard' | 'amex' | 'discover';
  creditLimit?: number;
  currentBalance: number;
  billingCycle: { start: number; end: number };
  dueDate: number;
  isActive: boolean;
  color?: string;
  currency?: Currency;
  secondaryCurrency?: Currency;
  secondaryCreditLimit?: number;
  secondaryCurrentBalance?: number;
}

// ==================== Loan ====================
export interface Loan extends BaseModel {
  name: string;
  // NOTE: 'home' was removed — home loans belong in the Mortgage module.
  // If you have a home loan, create a Mortgage record instead.
  type: 'personal' | 'auto' | 'education' | 'business' | 'other';
  lenderName: string;
  principalAmount: number;
  currentBalance: number;
  interestRate: number;
  termMonths: number;
  emiAmount: number;
  startDate: string;
  nextPaymentDate: string;
  nextPaymentAmount: number;
  paidAmount: number;
  paidInstallments: number;
  totalInstallments: number;
  status: 'active' | 'paused' | 'completed' | 'defaulted';
  // Payment history (consistent with Insurance.premiumPayments, Investment.transactions)
  payments: LoanPayment[];

  bankAccountId?: string;
  currency?: Currency;
}

export interface LoanPayment extends BaseModel {
  loanId: string;
  amount: number;
  principalComponent: number;
  interestComponent: number;
  paymentDate: string;
  paymentNumber: number;
  bankAccountId: string;
}

// ==================== Budget ====================
// DB DESIGN NOTE: allocatedAmount, availableBalance, remainingBalance, isOverBudget,
// overAmount, forecastedSpend, forecastGap, dailySafeSpend, requiredDailyReduction,
// requiredExtraIncome are COMPUTED fields. In the actual database schema, these should NOT
// be stored as columns — they should be calculated at query time from budget_amount and
// actual expense transactions. They are kept here for mock data convenience only.
export interface Budget extends BaseModel {
  name: string;
  month: string; // YYYY-MM
  currency?: Currency;
  totalBudgetAmount: number;
  allocatedAmount: number;
  availableBalance: number;
  remainingBalance: number;
  isOverBudget: boolean;
  overAmount: number;
  forecastedSpend: number;
  forecastGap: number;
  dailySafeSpend: number;
  requiredDailyReduction: number;
  requiredExtraIncome: number;
  categories: BudgetCategory[];
}

// Same DB DESIGN NOTE as Budget: allocatedAmount through requiredExtraIncome
// should be computed at query time, not stored as columns.
// NOTE: BudgetTransaction was removed from BudgetCategory. Budget spending should be
// computed from actual Expense records (via categoryId matching), not stored as
// duplicate transaction arrays. BudgetTransaction type retained for reference.
export interface BudgetCategory {
  id: string;
  name: string;
  categoryId: string;
  budgetAmount: number;
  allocatedAmount: number;
  availableBalance: number;
  remainingBalance: number;
  spentAmount: number;
  isOverBudget: boolean;
  overAmount: number;
  forecastedSpend: number;
  dailySafeSpend: number;
  requiredDailyReduction: number;
  requiredExtraIncome: number;
}

export interface BudgetTransaction {
  id: string;
  date: string;
  description: string;
  amount: number;
  categoryId: string;
}

// ==================== Dashboard ====================
export interface DashboardStats {
  totalBalance: number;
  totalIncome: number;
  totalExpense: number;
  totalSavings: number;
  incomeChangePercent: number;
  expenseChangePercent: number;
  savingsChangePercent: number;
  totalDebt: number;
  netWorth: number;
}

// ==================== Reports ====================
export interface ReportFilter {
  startDate: string;
  endDate: string;
  bankAccountIds?: string[];
  categoryIds?: string[];
  type?: 'income' | 'expense' | 'all';
}

// ==================== Invoice ====================
export type InvoiceStatus = 'draft' | 'sent' | 'viewed' | 'paid' | 'overdue' | 'cancelled';

export interface InvoiceItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
  total: number;
}

export interface Invoice extends BaseModel {
  invoiceNumber: string;       // e.g., INV-2026-001
  type: 'sent' | 'received';   // sent = I billed someone, received = someone billed me
  clientName: string;          // For sent: who I'm billing. For received: who billed me
  clientEmail?: string;
  clientPhone?: string;
  clientAddress?: string;
  items: InvoiceItem[];
  subtotal: number;
  taxRate: number;
  taxAmount: number;
  discountAmount: number;
  totalAmount: number;
  currency?: Currency;
  status: InvoiceStatus;
  issueDate: string;
  dueDate: string;
  paidDate?: string;
  notes?: string;
  bankAccountId?: string;      // Which bank account to receive payment into (for sent)
  tags?: string[];
}

export interface InvoiceFilter {
  status?: InvoiceStatus | InvoiceStatus[];
  startDate?: string;
  endDate?: string;
  clientName?: string;
  search?: string;
}

// ==================== Mortgage ====================
export type MortgageStatus = 'active' | 'paused' | 'completed' | 'defaulted' | 'in_review';

export interface MortgageProperty {
  name: string;
  propertyType: 'apartment' | 'house' | 'land' | 'commercial' | 'condo';
  address: string;
  sizeSqft?: number;
  purchasePrice: number;
  currentMarketValue?: number;
  purchaseDate: string;
}

export interface AmortizationEntry {
  installment: number;
  date: string;
  emiAmount: number;
  principalComponent: number;
  interestComponent: number;
  remainingBalance: number;
  isPaid: boolean;
}

export interface MortgageEscrow {
  propertyTaxAnnual: number;
  insuranceAnnual: number;
  monthlyEscrow: number;
}

export interface Mortgage extends BaseModel {
  property: MortgageProperty;
  lenderName: string;
  loanAmount: number;
  downPayment: number;
  downPaymentPercent: number;
  currentBalance: number;
  interestRate: number;
  interestType: 'fixed' | 'variable';
  termMonths: number;
  emiAmount: number;
  startDate: string;
  nextPaymentDate: string;
  paidAmount: number;
  paidInstallments: number;
  totalInstallments: number;
  status: MortgageStatus;
  escrow: MortgageEscrow;
  bankAccountId?: string;
  currency?: Currency;
  notes?: string;
}

// ==================== Held Mortgage (Lender Perspective) ====================
// When someone mortgaged THEIR property to YOU — you are the lender / income earner

export type HeldMortgageStatus = 'active' | 'paused' | 'completed' | 'defaulted' | 'foreclosed' | 'in_review';

export interface HeldMortgagePayment extends BaseModel {
  heldMortgageId: string;
  amount: number;
  principalComponent: number;
  interestComponent: number;
  paymentDate: string;
  paymentNumber: number;
  note?: string;
}

export interface HeldMortgageCollateral {
  name: string;
  propertyType: MortgageProperty['propertyType'];
  address: string;
  sizeSqft?: number;
  appraisedValue: number;
  currentValue: number;
  documents?: string; // deed reference or note
}

export interface HeldMortgage extends BaseModel {
  borrowerName: string;
  borrowerPhone?: string;
  borrowerEmail?: string;
  borrowerAddress?: string;
  relationship: 'family' | 'friend' | 'business' | 'colleague' | 'other';
  collateral: HeldMortgageCollateral;
  loanAmount: number;
  currentBalance: number;
  interestRate: number;
  interestType: 'fixed' | 'variable';
  termMonths: number;
  expectedMonthlyPayment: number;
  startDate: string;
  nextPaymentDueDate: string;
  totalReceivedAmount: number;
  totalInterestEarned: number;
  receivedInstallments: number;
  totalInstallments: number;
  status: HeldMortgageStatus;
  payments: HeldMortgagePayment[];
  latePaymentPenaltyRate: number; // % per month on overdue
  gracePeriodDays: number;
  bankAccountId?: string;
  currency?: Currency;
  notes?: string;
}

// ==================== Investments & Portfolio ====================

export type InvestmentCategory = 'fdr' | 'dps' | 'sanchaypatra' | 'stock' | 'mutual_fund' | 'gold' | 'bond' | 'other';
export type InvestmentStatus = 'active' | 'matured' | 'sold' | 'redeemed' | 'closed';
export type InvestmentTransactionType = 'buy' | 'sell' | 'dividend' | 'interest' | 'deposit' | 'withdrawal' | 'bonus' | 'maturity';

export interface InvestmentTransaction extends BaseModel {
  investmentId: string;
  type: InvestmentTransactionType;
  amount: number;
  units?: number;
  unitPrice?: number;
  date: string;
  note?: string;
  bankAccountId?: string;
}

export interface Investment extends BaseModel {
  name: string;
  category: InvestmentCategory;
  institution: string;
  accountNumber?: string;

  // Dates
  purchaseDate: string;
  maturityDate?: string; // for FDR, DPS, sanchaypatra, bond

  // Amount tracking
  investedAmount: number;     // total money put in (principal)
  currentValue: number;       // current market/realized value
  totalReturns: number;       // interest/dividends/capital gains received so far

  // Unit-based (stocks, gold, mutual_fund)
  quantity?: number;
  avgBuyPrice?: number;
  currentUnitPrice?: number;

  // Interest-based (FDR, DPS, sanchaypatra, bond)
  interestRate?: number;
  compounding?: 'monthly' | 'quarterly' | 'annually' | 'at_maturity';
  taxOnInterest?: boolean;

  // DPS specific
  monthlyDepositAmount?: number;
  totalDepositedSoFar?: number;
  depositCount?: number;

  // Stock specific
  stockSymbol?: string;
  stockExchange?: 'DSE' | 'CSE' | 'NASDAQ' | 'NYSE' | 'other';
  dividendYield?: number;

  // Gold specific
  purity?: '18k' | '21k' | '22k' | '24k';
  weightGrams?: number;

  // Status
  status: InvestmentStatus;
  autoRenew?: boolean;

  // Transactions
  transactions: InvestmentTransaction[];

  bankAccountId?: string;
  currency?: Currency;
  notes?: string;
  tags?: string[];
}

// ==================== Insurance ====================
export type InsuranceCategory = 'life' | 'health' | 'vehicle' | 'property' | 'travel' | 'critical_illness' | 'other';
export type InsuranceStatus = 'active' | 'expired' | 'cancelled' | 'claimed' | 'lapsed' | 'pending_renewal';
export type InsuranceClaimStatus = 'pending' | 'approved' | 'rejected' | 'paid' | 'in_review';

export interface InsuranceBeneficiary {
  name: string;
  relationship: 'self' | 'spouse' | 'child' | 'parent' | 'sibling' | 'other';
  percentage: number;
  phone?: string;
}

export interface InsurancePremiumPayment extends BaseModel {
  insuranceId: string;
  amount: number;
  paymentDate: string;
  paymentNumber: number;
  note?: string;
  bankAccountId?: string;
}

export interface InsuranceClaim extends BaseModel {
  insuranceId: string;
  claimNumber?: string;
  claimDate: string;
  claimAmount: number;
  approvedAmount?: number;
  status: InsuranceClaimStatus;
  description: string;
  documents?: string;
  resolutionDate?: string;
  resolutionNote?: string;
}

export interface Insurance extends BaseModel {
  name: string;
  category: InsuranceCategory;
  provider: string;              // Insurance company name
  policyNumber: string;
  groupPolicyNumber?: string;    // For employer-provided group insurance

  // Coverage & Premium
  coverageAmount: number;        // Sum assured / coverage limit
  premiumAmount: number;         // Per premium cycle
  premiumFrequency: 'monthly' | 'quarterly' | 'semiannually' | 'annually' | 'single';

  // Dates
  issueDate: string;
  startDate: string;
  expiryDate?: string;
  maturityDate?: string;         // For endowment / money-back policies
  nextPremiumDueDate?: string;

  // Payment tracking
  totalPremiumPaid: number;
  premiumPayments: InsurancePremiumPayment[];
  paidPremiumsCount: number;

  // Claims
  claims: InsuranceClaim[];
  totalClaimedAmount: number;

  // Beneficiaries
  beneficiaries: InsuranceBeneficiary[];

  // Status
  status: InsuranceStatus;
  autoRenew?: boolean;

  // Life specific
  policyTerm?: number;           // In years
  maturityBenefit?: number;
  riderNames?: string[];

  // Health specific
  deductibleAmount?: number;
  copayPercent?: number;
  networkHospitals?: string;

  // Vehicle specific
  vehicleType?: 'car' | 'motorcycle' | 'bus' | 'truck' | 'other';
  vehicleRegistration?: string;
  vehicleModel?: string;

  // Property specific
  propertyType?: 'apartment' | 'house' | 'land' | 'commercial' | 'other';
  propertyAddress?: string;
  propertyValue?: number;

  bankAccountId?: string;
  currency?: Currency;
  notes?: string;
  tags?: string[];
}

// ==================== Asset Register ====================
export type AssetCategory = 'real_estate' | 'vehicle' | 'electronics' | 'furniture' | 'jewelry' | 'art' | 'equipment' | 'other';
export type AssetStatus = 'owned' | 'rented' | 'leased' | 'sold' | 'gifted' | 'damaged' | 'disposed';
export type AssetCondition = 'excellent' | 'good' | 'fair' | 'poor' | 'damaged';
export type DepreciationMethod = 'none' | 'straight_line' | 'declining_balance';

export interface AssetValuation {
  date: string;
  value: number;
  note?: string;
}

export interface Asset extends BaseModel {
  name: string;
  category: AssetCategory;
  description?: string;

  // Purchase details
  purchaseDate: string;
  purchasePrice: number;
  purchaseFrom?: string;
  invoiceNumber?: string;

  // Current value
  currentValue: number;
  currentCondition: AssetCondition;
  valuations: AssetValuation[];  // value history for tracking appreciation/depreciation

  // Location
  location?: string;

  // Depreciation
  depreciationMethod: DepreciationMethod;
  usefulLifeYears?: number;
  salvageValue?: number;
  currentBookValue?: number;  // computed book value after depreciation

  // Real estate specific
  propertyType?: 'apartment' | 'house' | 'land' | 'commercial' | 'condo' | 'plot';
  propertyAddress?: string;
  sizeSqft?: number;
  floorNumber?: string;
  registrationDate?: string;
  registrationNumber?: string;
  khatianNumber?: string;

  // Vehicle specific
  vehicleType?: 'car' | 'motorcycle' | 'bus' | 'truck' | 'bicycle' | 'rickshaw_van' | 'other';
  vehicleBrand?: string;
  vehicleModel?: string;
  vehicleYear?: number;
  vehicleRegistrationNo?: string;
  engineNo?: string;
  chassisNo?: string;
  mileageKm?: number;

  // Electronics specific
  brand?: string;
  model?: string;
  serialNumber?: string;
  warrantyExpiryDate?: string;

  // Jewelry specific
  itemType?: 'necklace' | 'ring' | 'earring' | 'bangle' | 'bracelet' | 'chain' | 'pendant' | 'watch' | 'set' | 'other';
  material?: string;
  weightGrams?: number;
  purity?: string;

  // Status & ownership
  status: AssetStatus;
  ownershipPercentage?: number;  // for co-owned assets (default 100)
  loanAgainstAsset?: boolean;    // is there an active loan/mortgage against this asset
  insurancePolicyId?: string;    // link to insurance policy if applicable

  // Shared with / Co-owners
  coOwners?: string;

  bankAccountId?: string;
  currency?: Currency;
  notes?: string;
  tags?: string[];
}

// ==================== Lending ====================
export type LendingStatus = 'active' | 'partially_repaid' | 'fully_repaid' | 'overdue' | 'defaulted' | 'cancelled';

export interface LendingPayment extends BaseModel {
  lendingId: string;
  amount: number;
  paymentDate: string;
  paymentNumber: number;
  note?: string;
}

export interface Lending extends BaseModel {
  borrowerName: string;
  borrowerPhone?: string;
  borrowerEmail?: string;
  relationship: 'family' | 'friend' | 'colleague' | 'business' | 'other';
  principalAmount: number;
  currentBalance: number;
  interestRate: number;
  totalInterestAmount: number;
  totalRepayableAmount: number;
  totalRepaidAmount: number;
  issuedDate: string;
  dueDate?: string;
  repaymentSchedule?: 'lump_sum' | 'monthly' | 'weekly' | 'custom';
  status: LendingStatus;
  notes?: string;
  tags?: string[];
  currency?: Currency;
}

// ==================== Document Vault ====================
export type DocumentCategory = 'tax_return' | 'insurance_policy' | 'property_deed' | 'bank_statement' | 'investment_statement' | 'loan_document' | 'contract' | 'receipt' | 'invoice' | 'id_proof' | 'medical_record' | 'education_certificate' | 'vehicle_registration' | 'other';
export type DocumentFormat = 'pdf' | 'doc' | 'docx' | 'xls' | 'xlsx' | 'jpg' | 'jpeg' | 'png' | 'csv' | 'txt' | 'zip' | 'other';
export type DocumentStatus = 'active' | 'expired' | 'archived' | 'draft';

export interface DocumentVersion {
  versionNumber: number;
  date: string;
  note?: string;
  fileSize: number;
}

export interface DocumentFolder {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  parentFolderId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentVaultItem extends BaseModel {
  name: string;
  description?: string;
  category: DocumentCategory;
  format: DocumentFormat;
  status: DocumentStatus;

  // File info (mock — actual files not stored)
  fileSize: number;            // bytes
  filePath?: string;           // simulated path
  fileName?: string;           // original filename

  // Organization
  folderId?: string;
  tags: string[];
  isFavorite: boolean;
  isImportant: boolean;

  // Dates
  documentDate?: string;       // date the document was issued/created (e.g., tax year, policy date)
  expiryDate?: string;         // document expiry/validity
  reminderBeforeDays?: number; // days before expiry to show alert

  // Linked entities (optional references to other parts of FinLife)
  linkedEntityId?: string;     // ID of linked entity (insurance, loan, asset, etc.)
  linkedEntityType?: 'insurance' | 'loan' | 'mortgage' | 'asset' | 'investment' | 'lending' | 'invoice' | 'other';

  // Versioning
  currentVersion: number;
  versions: DocumentVersion[];

  // Sharing & access
  sharedWith?: string;         // names of people with access
  isEncrypted?: boolean;

  // Metadata
  uploadedBy?: string;
  source?: string;             // where doc came from (e.g., email, upload, scanned, download)

  notes?: string;
}

// ==================== Financial Calendar ====================
export type CalendarEventCategory = 'emi_payment' | 'insurance_premium' | 'bill_payment' | 'investment_maturity' | 'investment_deposit' | 'dividend' | 'tax_deadline' | 'salary' | 'rental_income' | 'rental_payment' | 'lending_payment' | 'subscription' | 'maintenance' | 'document_renewal' | 'milestone' | 'other';
export type CalendarEventStatus = 'upcoming' | 'completed' | 'overdue' | 'cancelled';
export type RecurrencePattern = 'none' | 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'quarterly' | 'semiannually' | 'annually' | 'custom';

export interface CalendarEvent extends BaseModel {
  title: string;
  description?: string;
  category: CalendarEventCategory;
  status: CalendarEventStatus;

  // Amount (optional — not all events have monetary value)
  amount?: number;
  currency?: Currency;

  // Dates
  eventDate: string;              // the date this event occurs
  endDate?: string;               // for recurring events, when recurrence ends
  dueDate?: string;               // for events with a due window (e.g., tax filing deadline)

  // Recurrence
  recurrence: RecurrencePattern;
  customRecurrenceDays?: number;  // for custom recurrence (every N days)
  recurrenceDayOfMonth?: number;  // for monthly/quarterly (e.g., 5th of each month)
  nextOccurrenceDate?: string;    // computed next date after eventDate

  // Reminders
  reminderDaysBefore: number;     // how many days before to show alert (0 = same day)
  reminderEnabled: boolean;
  secondReminderDaysBefore?: number;

  // Color coding
  color?: string;                 // hex color for calendar dot

  // Linked entity
  linkedEntityId?: string;
  linkedEntityType?: 'loan' | 'mortgage' | 'insurance' | 'investment' | 'lending' | 'invoice' | 'document' | 'card' | 'bill' | 'other';
  linkedBillId?: string;           // Direct link to a Bill record

  // Priority
  priority: 'low' | 'medium' | 'high';

  notes?: string;
  tags?: string[];
}

// ==================== Bills ====================
export type BillCategory = 'rent' | 'utilities' | 'subscriptions' | 'loan_emi' | 'insurance_premium' | 'credit_card' | 'medical' | 'education' | 'vehicle' | 'service_contract' | 'tax' | 'other';
export type BillStatus = 'upcoming' | 'due_soon' | 'overdue' | 'paid' | 'skipped' | 'cancelled';
export type BillRecurrence = 'none' | 'weekly' | 'biweekly' | 'monthly' | 'quarterly' | 'semiannually' | 'annually';

export interface BillPaymentHistory {
  id: string;
  paymentDate: string;
  amount: number;
  paymentMethod: string;
  referenceNumber?: string;
  note?: string;
}

export interface Bill extends BaseModel {
  name: string;
  description?: string;
  category: BillCategory;
  status: BillStatus;

  // Amount
  amount: number;
  currency?: Currency;

  // Payee / Vendor
  payeeName: string;
  payeeAccount?: string;
  payeeWebsite?: string;

  // Due Date
  dueDate: string;
  dueDateDayOfMonth?: number;

  // Grace period & late fee
  gracePeriodDays?: number;
  lateFeeAmount?: number;
  lateFeePercent?: number;

  // Recurrence
  recurrence: BillRecurrence;
  recurrenceDayOfMonth?: number;
  endDate?: string;

  // Auto-pay
  autoPayEnabled: boolean;
  autoPayMethod?: string;
  autoPayDayBefore?: number;

  // Payment tracking
  paymentHistory: BillPaymentHistory[];
  totalPaidAmount: number;
  totalPaymentsCount: number;
  lastPaidDate?: string;
  lastPaidAmount?: number;

  // Reminders
  reminderDaysBefore: number;
  reminderEnabled: boolean;

  // Priority
  priority: 'low' | 'medium' | 'high';

  // Linked entity
  linkedEntityId?: string;
  linkedEntityType?: 'loan' | 'mortgage' | 'insurance' | 'investment' | 'card' | 'invoice' | 'calendar' | 'other';
  linkedCalendarEventId?: string;

  // Payment account
  preferredPaymentAccountId?: string;

  notes?: string;
  tags?: string[];
}

// ==================== Savings Goals ====================
export type SavingsGoalCategory = 'emergency_fund' | 'vacation' | 'home' | 'car' | 'education' | 'wedding' | 'retirement' | 'gadget' | 'gift' | 'medical' | 'other';
export type SavingsGoalStatus = 'active' | 'paused' | 'completed' | 'abandoned';

export interface SavingsGoalContribution {
  id: string;
  amount: number;
  date: string;
  note?: string;
  bankAccountId?: string;
}

export interface SavingsGoalMilestone {
  id: string;
  percent: number;        // 10, 25, 50, 75, 100
  label: string;          // e.g., "Quarter Way", "Halfway There", "Almost There", "Goal Complete!"
  achieved: boolean;
  achievedDate?: string;
}

export interface SavingsGoal extends BaseModel {
  name: string;
  description?: string;
  category: SavingsGoalCategory;
  status: SavingsGoalStatus;

  // Target & Progress
  targetAmount: number;
  currentAmount: number;
  currency?: Currency;

  // Dates
  startDate: string;
  targetDate?: string;           // Optional deadline
  completedDate?: string;        // When 100% reached

  // Monthly Contribution Plan
  monthlyContributionAmount: number;
  autoContributeEnabled: boolean;
  autoContributeDayOfMonth?: number;

  // Contribution tracking
  contributions: SavingsGoalContribution[];
  totalContributed: number;
  totalWithdrawn: number;
  contributionCount: number;

  // Milestones (auto-generated at 25%, 50%, 75%, 100%)
  milestones: SavingsGoalMilestone[];

  // Motivation
  motivationalQuote?: string;
  coverColor?: string;           // hex color for the goal card accent
  coverIcon?: string;

  // Streak
  currentStreak: number;         // consecutive months with contributions
  longestStreak: number;

  // Priority
  priority: 'low' | 'medium' | 'high';

  // Linked
  bankAccountId?: string;

  notes?: string;
  tags?: string[];
}
