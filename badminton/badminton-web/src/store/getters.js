const getters = {
  category: state => state.category,
  device: state => state.app.device,
  token: state => state.app.token,
  user: state => state.app.user,
  menuConfig: state => state.app.menuConfig
}
export default getters
