import { Admin, CustomRoutes, Resource } from "react-admin";
import { Route } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import polyglotI18nProvider from "ra-i18n-polyglot";
import ukrainianMessages from "ra-language-ukrainian";
import { authProvider } from "./authProvider";
import { dataProvider } from "./dataProvider";
import { LoginPage } from "./LoginPage";
import { RouteReportEdit, RouteReportList } from "./resources/routeReports";
import { ExpenseCreate, ExpenseEdit, ExpenseList } from "./resources/expenses";
import { UserCreate, UserEdit, UserList } from "./resources/users";
import { VehicleCreate, VehicleEdit, VehicleList } from "./resources/vehicles";
import { Summary } from "./pages/Summary";

// Переводит встроенные элементы react-admin (кнопки Save/Delete, пагинация,
// форма входа и т.д.) — без этого они остались бы на английском, а наши
// собственные подписи были бы на украинском: получился бы разнобой языков.
// ra-language-ukrainian собран под ra-core@4 и несёт свой (структурно
// идентичный) тип TranslationMessages — отсюда приведение типа ниже.
const i18nProvider = polyglotI18nProvider(() => ukrainianMessages as never, "uk");

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

function App() {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <Admin
        authProvider={authProvider}
        dataProvider={dataProvider}
        i18nProvider={i18nProvider}
        loginPage={LoginPage}
        title="GIP Trans — Керування"
      >
        <Resource name="route-reports" list={RouteReportList} edit={RouteReportEdit} options={{ label: "Рейси" }} />
        <Resource name="expenses" list={ExpenseList} create={ExpenseCreate} edit={ExpenseEdit} options={{ label: "Витрати" }} />
        <Resource name="users" list={UserList} create={UserCreate} edit={UserEdit} options={{ label: "Користувачі" }} />
        <Resource name="vehicles" list={VehicleList} create={VehicleCreate} edit={VehicleEdit} options={{ label: "Автомобілі" }} />
        <CustomRoutes>
          <Route path="/summary" element={<Summary />} />
        </CustomRoutes>
      </Admin>
    </GoogleOAuthProvider>
  );
}

export default App;
