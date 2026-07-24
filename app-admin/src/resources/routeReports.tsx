import {
  Datagrid,
  DateField,
  Edit,
  List,
  NumberField,
  NumberInput,
  SelectField,
  SelectInput,
  SimpleForm,
  TextField,
  TextInput,
} from "react-admin";

const STATUS_CHOICES = [
  { id: "draft", name: "Чернетка" },
  { id: "submitted", name: "Надіслано" },
  { id: "approved", name: "Підтверджено" },
  { id: "rejected", name: "Відхилено" },
];

export function RouteReportList() {
  return (
    <List sort={{ field: "report_date", order: "DESC" }}>
      <Datagrid rowClick="edit">
        <DateField source="report_date" label="Дата" />
        <TextField source="vehicle_plate" label="Держ.номер" />
        <TextField source="route_from" label="Звідки" />
        <TextField source="route_to" label="Куди" />
        <NumberField source="mileage" label="Пробіг, км" />
        <TextField source="waybill_number" label="ТТН" />
        <TextField source="client_name" label="Клієнт" />
        <NumberField source="revenue_amount" label="Виручка" />
        <SelectField source="status" label="Статус" choices={STATUS_CHOICES} />
      </Datagrid>
    </List>
  );
}

export function RouteReportEdit() {
  return (
    <Edit>
      <SimpleForm>
        {/* Данные рейса — вводит водитель, здесь только для справки */}
        <TextField source="report_date" label="Дата" />
        <TextField source="vehicle_plate" label="Держ.номер" />
        <TextField source="route_from" label="Звідки" />
        <TextField source="route_to" label="Куди" />
        <NumberField source="mileage" label="Пробіг, км" />

        {/* Поля, которые проставляет PO/бухгалтер */}
        <TextInput source="waybill_number" label="Номер ТТН" />
        <TextInput source="client_name" label="Клієнт" />
        <NumberInput source="revenue_amount" label="Виручка" />
        <SelectInput source="status" label="Статус" choices={STATUS_CHOICES} />
      </SimpleForm>
    </Edit>
  );
}
