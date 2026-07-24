import { Admin, CustomRoutes, Resource } from "react-admin";
import { Route } from "react-router-dom";
import polyglotI18nProvider from "ra-i18n-polyglot";
import ukrainianMessages from "ra-language-ukrainian";
import { authProvider } from "./authProvider";
import { dataProvider } from "./dataProvider";
import { RouteReportEdit, RouteReportList } from "./resources/routeReports";
import { ExpenseCreate, ExpenseEdit, ExpenseList } from "./resources/expenses";
import { Summary } from "./pages/Summary";

// Переводит встроенные элементы react-admin (кнопки Save/Delete, пагинация,
// форма входа и т.д.) — без этого они остались бы на английском, а наши
// собственные подписи были бы на украинском: получился бы разнобой языков.
// ra-language-ukrainian собран под ra-core@4 и несёт свой (структурно
// идентичный) тип TranslationMessages — отсюда приведение типа ниже.
const i18nProvider = polyglotI18nProvider(() => ukrainianMessages as never, "uk");

function App() {
  return (
    <Admin authProvider={authProvider} dataProvider={dataProvider} i18nProvider={i18nProvider} title="GIP Trans — Керування">
      <Resource name="route-reports" list={RouteReportList} edit={RouteReportEdit} options={{ label: "Рейси" }} />
      <Resource name="expenses" list={ExpenseList} create={ExpenseCreate} edit={ExpenseEdit} options={{ label: "Витрати" }} />
      <CustomRoutes>
        <Route path="/summary" element={<Summary />} />
      </CustomRoutes>
    </Admin>
  );
}

export default App;
