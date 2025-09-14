# UX Design & Implementation Prompt for PDF Transaction Extractor

## Design Approach

### Design System Methodology
**Atomic Design with Component-Driven Development**
- Build UI using atoms (buttons, inputs), molecules (search bars, cards), organisms (tables, headers), templates (page layouts), and pages (complete screens)
- Create reusable component library with design tokens for colors, spacing, and typography
- Implement consistent design patterns across all interface elements

### Visual Design Trend
**Clean Minimalism with Subtle Glassmorphism**
- Use maximum whitespace and purposeful content density
- Apply subtle glassmorphism effects for modals and overlays (translucent backgrounds with blur)
- Implement soft shadows and refined borders for depth without visual noise
- Focus on functional hierarchy where important actions are most prominent

### Interaction Pattern
**Progressive Disclosure with Contextual Actions**
- Reveal complexity only when needed - start simple, add detail progressively
- Show contextual tools and actions only when relevant (zoom controls on PDF hover, bulk actions when rows selected)
- Use smart defaults and anticipatory design to reduce user cognitive load

## Implementation Instructions

### Layout Structure
Create a split-screen layout with:
- **Header**: 60px fixed height with app branding and status indicators
- **Main Content**: 60/40 split between PDF viewer (left) and transaction table (right)
- **PDF Panel**: Exclusively for PDF display with upload zone and viewer controls
- **Transaction Panel**: 7-column data table with summary cards and bulk actions

### Color Palette
- **Primary Brand**: #3B82F6 (blue) for actions and focus states
- **Text Hierarchy**: #111827 (primary), #6B7280 (secondary), #9CA3AF (muted)
- **Backgrounds**: #FFFFFF (main), #F8FAFC (panels), #F3F4F6 (subtle highlights)
- **Semantic Colors**: #059669 (success/credits), #DC2626 (error/debits), #D97706 (warnings)

### Typography System
- **Font**: Geist or system-ui fallback (not Apple-specific fonts)
- **Scale**: 32px (h1), 20px (h2), 16px (body), 14px (table), 12px (captions)
- **Weights**: 400 (regular), 500 (medium), 600 (semibold), 700 (bold headings only)

### ShadCN Components to Use
- **Table Structure**: `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableCell`
- **Interactive Elements**: `Button`, `Input`, `Select`, `Checkbox`, `DropdownMenu`
- **Feedback**: `Badge`, `Alert`, `Progress`, `Skeleton`, `Toast`
- **Layout**: `Card`, `Dialog`, `Pagination`, `ScrollArea`

### Table Design (7 Columns)
1. **Selection** (40px) - Checkboxes for bulk actions
2. **Date** (100px) - Sortable date column 
3. **Description** (flex-1) - Primary transaction description
4. **Amount** (120px) - Right-aligned, color-coded monetary values
5. **Type** (100px) - Badge components for Credit/Debit
6. **Category** (120px) - Editable dropdown for transaction categorization
7. **Actions** (80px) - Dropdown menu with edit/delete options

### Key Features to Implement
- **Upload Flow**: Drag-and-drop zone with visual feedback and password modal
- **Real-time Processing**: Progress indicators and WebSocket status updates
- **PDF Navigation**: Page controls with zoom and navigation synchronized to transactions
- **Table Interactions**: Sorting, filtering, bulk selection, inline editing
- **Responsive Design**: Adapt layout for mobile (stacked) and tablet (adjusted ratios)

### Animation Guidelines
- **Timing**: 150ms (hover), 250ms (transitions), 400ms (page changes)
- **Easing**: ease-out for entrances, ease-in for exits
- **Micro-interactions**: Button press feedback, loading states, hover effects

### States to Design
- **Upload State**: Clean drag-and-drop zone with clear call-to-action
- **Processing State**: Progress bars with meaningful status messages
- **Loading State**: Skeleton components maintaining layout structure
- **Empty State**: Helpful messaging with next action guidance
- **Error State**: Clear error messages with recovery options

### Accessibility Requirements
- Proper color contrast ratios (WCAG 2.1 AA)
- Keyboard navigation for all interactive elements
- Screen reader support with semantic HTML and ARIA labels
- Focus indicators for all interactive components

### Implementation Priority
1. Basic layout with header and split panels
2. PDF upload zone and viewer controls
3. Transaction table with ShadCN components
4. Real-time data updates and state management
5. Polish with animations and micro-interactions

Build this as a modern, professional interface that prioritizes usability and visual clarity while maintaining sophisticated aesthetics suitable for financial data processing.