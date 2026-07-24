export interface FuelRefillInput {
  refillDatetime: string; // ISO datetime-local value
  stationName: string;
  liters: string;
  totalCost: string;
  receiptPhotoUrl?: string;
}

export interface RouteReportInput {
  vehiclePlate: string;
  reportDate: string;
  routeFrom: string;
  routeTo: string;
  odometerStart: string;
  odometerEnd: string;
  fuelEnd: string;
  departureTime: string;
  arrivalTime: string;
  comment: string;
  fuelRefills: FuelRefillInput[];
}

export interface RouteReportCreatePayload {
  vehicle_plate: string;
  report_date: string;
  route_from: string;
  route_to: string;
  odometer_start: number;
  odometer_end: number;
  fuel_end: number;
  departure_time: string;
  arrival_time: string;
  comment: string | null;
  fuel_refills: {
    refill_datetime: string;
    station_name: string;
    liters: number;
    total_cost: number;
    receipt_photo_url: string | null;
  }[];
}
