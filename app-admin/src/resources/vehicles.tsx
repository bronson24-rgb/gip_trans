import {
  BooleanField,
  BooleanInput,
  Create,
  Datagrid,
  Edit,
  List,
  required,
  SimpleForm,
  TextField,
  TextInput,
} from "react-admin";

function VehicleForm() {
  return (
    <SimpleForm>
      <TextInput source="plate_number" label="Держ.номер" validate={required()} />
      <TextInput source="make" label="Марка" />
      <TextInput source="model" label="Модель" />
      <BooleanInput source="is_active" label="Активний" defaultValue={true} />
    </SimpleForm>
  );
}

export function VehicleList() {
  return (
    <List sort={{ field: "plate_number", order: "ASC" }}>
      <Datagrid rowClick="edit">
        <TextField source="plate_number" label="Держ.номер" />
        <TextField source="make" label="Марка" />
        <TextField source="model" label="Модель" />
        <BooleanField source="is_active" label="Активний" />
      </Datagrid>
    </List>
  );
}

export function VehicleCreate() {
  return (
    <Create>
      <VehicleForm />
    </Create>
  );
}

export function VehicleEdit() {
  return (
    <Edit>
      <VehicleForm />
    </Edit>
  );
}
