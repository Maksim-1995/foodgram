import {
  Container,
  Input,
  FormTitle,
  Main,
  Form,
  Button,
} from "../../components";
import styles from "./styles.module.css";
import { useFormWithValidation } from "../../utils";
import { Redirect } from "react-router-dom";
import { useContext } from "react";
import { AuthContext } from "../../contexts";
import { Helmet } from "react-helmet-async";

const SignUp = ({ onSignUp, submitError, setSubmitError }) => {
  const { values, handleChange, errors } = useFormWithValidation();
  const authContext = useContext(AuthContext);

  const onChange = (e) => {
    setSubmitError({ submitError: "" });
    handleChange(e);
  };

  return (
    <Main withBG asFlex>
      {authContext && <Redirect to="/recipes" />}
      <Container className={styles.center}>
        <Helmet>
          <title>Регистрация</title>
          <meta
            name="description"
            content="Фудграм - Регистрация"
          />
          <meta property="og:title" content="Регистрация" />
        </Helmet>
        <Form
          className={styles.form}
          onSubmit={(e) => {
            e.preventDefault();
            onSignUp(values);
          }}
        >
          <FormTitle>Регистрация</FormTitle>
          <Input
            placeholder="Имя"
            name="first_name"
            required
            isAuth={true}
            error={errors}
            onChange={onChange}
          />
          <Input
            placeholder="Фамилия"
            name="last_name"
            required
            isAuth={true}
            error={errors}
            onChange={onChange}
          />
          <Input
            placeholder="Имя пользователя"
            name="username"
            required
            isAuth={true}
            error={errors}
            onChange={onChange}
          />

          <Input
            placeholder="Адрес электронной почты"
            name="email"
            required
            isAuth={true}
            error={errors}
            onChange={onChange}
          />
          <Input
            placeholder="Пароль"
            type="password"
            name="password"
            required
            isAuth={true}
            error={errors}
            submitError={submitError}
            onChange={onChange}
          />
          <Button modifier="style_dark" type="submit" className={styles.button}>
            Создать аккаунт
          </Button>
        </Form>
      </Container>
    </Main>
  );
};

export default SignUp;
