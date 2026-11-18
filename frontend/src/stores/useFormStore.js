// src/stores/useFormStore.js
import { defineStore } from 'pinia'
import { reactive, ref } from 'vue'
import axios from 'axios'

const API_BASE = ''

export const useFormStore = defineStore('form', () => {
  const form = reactive({
    file_cur: '', file_pri: '',
    cur_coordX: -128.69, cur_coordY: -175.31, cur_coordZ: -298.38,
    pri_coordX: -128.69, pri_coordY: -175.31, pri_coordZ: -298.38,
    months: 12
  })

  function saveForm() {}

  const isLoggedIn = ref(false)
  const userId = ref(null)
  const doctorName = ref('')
  const role = ref('doctor')

  async function login(name, selectedRole, password) {
    const formData = new FormData()
    formData.append('username', name)
    formData.append('password', password)
    formData.append('role', selectedRole)

    try {
      const res = await axios.post(`${API_BASE}/api/auth/login`, formData)
      if (res.data.status === 'success') {
        isLoggedIn.value = true
        userId.value = res.data.user_id
        doctorName.value = res.data.username
        role.value = res.data.role
        await fetchHistory()
        return { success: true }
      }
    } catch (e) {
      return { success: false, msg: e.response?.data?.detail || '登录失败' }
    }
  }

  async function register(name, selectedRole, password) {
    const formData = new FormData()
    formData.append('username', name)
    formData.append('password', password)
    formData.append('role', selectedRole)

    try {
      const res = await axios.post(`${API_BASE}/api/auth/register`, formData)
      if (res.data.status === 'success') {
        return { success: true }
      }
    } catch (e) {
      return { success: false, msg: e.response?.data?.detail || '注册失败' }
    }
  }

  function logout() {
    isLoggedIn.value = false
    userId.value = null
    historyRecords.value = []
  }

  const historyRecords = ref([])

  async function fetchHistory() {
    if (!userId.value) return
    try {
      const res = await axios.get(`${API_BASE}/api/history?user_id=${userId.value}`)
      historyRecords.value = res.data
    } catch (e) { console.error(e) }
  }

  async function addHistory(record) {
    if (!userId.value) return
    const formData = new FormData()
    formData.append('user_id', userId.value)
    formData.append('risk_level', record.risk_level)
    formData.append('risk_prob', record.risk_prob)
    formData.append('volume_mm3', record.volume_mm3)
    try {
      await axios.post(`${API_BASE}/api/history`, formData)
      await fetchHistory()
    } catch (e) { console.error(e) }
  }

  return { form, saveForm, isLoggedIn, userId, doctorName, role, login, register, logout, historyRecords, fetchHistory, addHistory }
})