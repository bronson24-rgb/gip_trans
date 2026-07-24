export interface FuelRefillInput {
  refillDatetime: string; // ISO datetime-local value
  stationName: string;
  liters: string;
  totalCost: string;
  receiptPhotoKey?: string;
}

export interface RouteReportInput {
  vehicleId: string;
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

export interface Vehicle {
  id: string;
  plate_number: string;
  make: string | null;
  model: string | null;
  is_active: boolean;
}

export interface RouteReportCreatePayload {
  vehicle_id: string;
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
    receipt_photo_key: string | null;
  }[];
}
