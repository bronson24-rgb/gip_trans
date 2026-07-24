import {
  Create,
  Datagrid,
  DateField,
  DateInput,
  Edit,
  List,
  NumberField,
  NumberInput,
  required,
  SelectField,
  SelectInput,
  SimpleForm,
  TextField,
  TextInput,
} from "react-admin";

const CATEGORY_CHOICES = [
  { id: "salary", name: "Зарплата" },
  { id: "rent", name: "Оренда" },
  { id: "insurance", name: "Страховка" },
  { id: "tax", name: "Податки" },
  { id: "maintenance", name: "Обслуговування" },
  { id: "other", name: "Інше" },
];

function ExpenseForm() {
  return (
    <SimpleForm>
      <DateInput source="expense_date" label="Дата" validate={required()} />
      <SelectInput source="category" label="Категорія" choices={CATEGORY_CHOICES} validate={required()} />
      <NumberInput source="amount" label="Сума" validate={required()} />
      <TextInput source="comment" label="Коментар" multiline />
    </SimpleForm>
  );
}

export function ExpenseList() {
  return (
    <List sort={{ field: "expense_date", order: "DESC" }}>
      <Datagrid rowClick="edit">
        <DateField source="expense_date" label="Дата" />
        <SelectField source="category" label="Категорія" choices={CATEGORY_CHOICES} />
        <NumberField source="amount" label="Сума" />
        <TextField source="comment" label="Коментар" />
      </Datagrid>
    </List>
  );
}

export function ExpenseCreate() {
  return (
    <Create>
      <ExpenseForm />
    </Create>
  );
}

export function ExpenseEdit() {
  return (
    <Edit>
      <ExpenseForm />
    </Edit>
  );
}
