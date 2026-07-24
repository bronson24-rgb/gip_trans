import {
  BooleanField,
  BooleanInput,
  Create,
  Datagrid,
  DateField,
  Edit,
  List,
  required,
  SelectField,
  SelectInput,
  SimpleForm,
  TextField,
  TextInput,
} from "react-admin";

const ROLE_CHOICES = [
  { id: "driver", name: "Водій" },
  { id: "accountant", name: "Бухгалтер" },
  { id: "admin", name: "Адміністратор" },
];

export function UserList() {
  return (
    <List sort={{ field: "email", order: "ASC" }}>
      <Datagrid rowClick="edit">
        <TextField source="email" label="Email" />
        <TextField source="full_name" label="Ім'я" />
        <SelectField source="role" label="Роль" choices={ROLE_CHOICES} />
        <BooleanField source="is_allowed" label="Доступ дозволено" />
        <DateField source="created_at" label="Створено" showTime />
      </Datagrid>
    </List>
  );
}

export function UserCreate() {
  return (
    <Create>
      <SimpleForm>
        <TextInput source="email" label="Email" type="email" validate={required()} />
        <TextInput source="full_name" label="Ім'я" />
        <SelectInput source="role" label="Роль" choices={ROLE_CHOICES} defaultValue="driver" validate={required()} />
        <BooleanInput source="is_allowed" label="Доступ дозволено" defaultValue={true} />
      </SimpleForm>
    </Create>
  );
}

export function UserEdit() {
  return (
    <Edit>
      <SimpleForm>
        <TextField source="email" label="Email" />
        <TextInput source="full_name" label="Ім'я" />
        <SelectInput source="role" label="Роль" choices={ROLE_CHOICES} validate={required()} />
        <BooleanInput source="is_allowed" label="Доступ дозволено" />
      </SimpleForm>
    </Edit>
  );
}
