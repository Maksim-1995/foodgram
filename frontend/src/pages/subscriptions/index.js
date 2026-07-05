import { Title, Pagination, Container, Main, SubscriptionList  } from '../../components'
import { useSubscriptions } from '../../utils'
import api from '../../api'
import { useEffect } from 'react'
import { Helmet } from 'react-helmet-async'

const SubscriptionsPage = () => {
  const {
    subscriptions,
    setSubscriptions,
    subscriptionsCount,
    setSubscriptionsCount,
    removeSubscription,
    subscriptionsPage,
    setSubscriptionsPage
  } = useSubscriptions()

  const getSubscriptions = ({ page }) => {
    api
      .getSubscriptions({ page })
      .then(res => {
        setSubscriptions(res.results)
        setSubscriptionsCount(res.count)
      })
  }

  useEffect(_ => {
    getSubscriptions({ page: subscriptionsPage })
  }, [subscriptionsPage])


  return <Main>
    <Container>
      <Helmet>
        <title>Мои подписки</title>
        <meta name="description" content="Фудграм - Мои подписки" />
        <meta property="og:title" content="Мои подписки" />
      </Helmet>
      <Title
        title='Мои подписки'
      />
      <SubscriptionList
        subscriptions={subscriptions}
        removeSubscription={removeSubscription}
      />
      <Pagination
        count={subscriptionsCount}
        limit={6}
        onPageChange={page => {
          setSubscriptionsPage(page)
        }}
      />
    </Container>
  </Main>
}

export default SubscriptionsPage