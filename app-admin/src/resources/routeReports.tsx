import {
  ArrayField,
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
  useRecordContext,
} from "react-admin";
import { Button } from "@mui/material";
import { authenticatedFetch } from "../apiClient";

const STATUS_CHOICES = [
  { id: "draft", name: "Чернетка" },
  { id: "submitted", name: "Надіслано" },
  { id: "approved", name: "Підтверджено" },
  { id: "rejected", name: "Відхилено" },
];

// Bucket приватний, файл віддається через тимчасове presigned-посилання
// (GET /api/uploads/receipt/{key}, потребує Bearer-токен — звичайне <a href>
// його не надішле, тому йдемо через fetch і відкриваємо вже підписане посилання.
function ReceiptButton() {
  const refill = useRecordContext<{ receipt_photo_key?: string | null }>();
  if (!refill?.receipt_photo_key) return <span>—</span>;

  const handleClick = async () => {
    const response = await authenticatedFetch(`/api/uploads/receipt/${refill.receipt_photo_key}`);
    if (!response.ok) return;
    window.open(response.url, "_blank", "noopener,noreferrer");
  };

  return (
    <Button size="small" onClick={handleClick}>
      Переглянути чек
    </Button>
  );
}

export function RouteReportList() {
  return (
    <List sort={{ field: "report_date", order: "DESC" }}>
      <Datagrid rowClick="edit">
        <DateField source="report_date" label="Дата" />
        <TextField source="vehicle.plate_number" label="Держ.номер" />
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
        <TextField source="vehicle.plate_number" label="Держ.номер" />
        <TextField source="route_from" label="Звідки" />
        <TextField source="route_to" label="Куди" />
        <NumberField source="mileage" label="Пробіг, км" />

        <ArrayField source="fuel_refills" label="Заправки">
          <Datagrid bulkActionButtons={false}>
            <DateField source="refill_datetime" label="Дата і час" showTime />
            <TextField source="station_name" label="АЗС" />
            <NumberField source="liters" label="Літри" />
            <NumberField source="total_cost" label="Сума" />
            <ReceiptButton />
          </Datagrid>
        </ArrayField>

        {/* Поля, которые проставляет PO/бухгалтер */}
        <TextInput source="waybill_number" label="Номер ТТН" />
        <TextInput source="client_name" label="Клієнт" />
        <NumberInput source="revenue_amount" label="Виручка" />
        <SelectInput source="status" label="Статус" choices={STATUS_CHOICES} />
      </SimpleForm>
    </Edit>
  );
}
