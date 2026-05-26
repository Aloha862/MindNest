<template>
  <main>
    <PageHeader title="用户管理" :subtitle="`共 ${total} 个用户`" />
    <AdminTable :rows="rows" :loading="loading" :total="total" :page="page" :page-size="pageSize" placeholder="搜索用户名或昵称" @search="onSearch" @page-change="onPageChange">
      <template #filters>
        <el-select v-model="role" placeholder="全部角色" clearable @change="refresh"><el-option label="普通用户" value="user" /><el-option label="管理员" value="admin" /></el-select>
        <el-select v-model="status" placeholder="全部状态" clearable @change="refresh"><el-option label="已激活" value="active" /><el-option label="已禁用" value="disabled" /></el-select>
      </template>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="nickname" label="昵称" />
      <el-table-column prop="phone" label="手机号" />
      <el-table-column label="角色"><template #default="{ row }"><el-tag :type="row.role === 'admin' ? 'primary' : 'info'">{{ row.role === 'admin' ? '管理员' : '普通用户' }}</el-tag></template></el-table-column>
      <el-table-column label="状态"><template #default="{ row }"><StatusTag :status="row.status" /></template></el-table-column>
      <el-table-column prop="createdAt" label="注册时间" width="180" />
      <el-table-column prop="lastLoginTime" label="最近登录" width="180" />
      <el-table-column label="操作" width="130">
        <template #default="{ row }">
          <div class="table-actions">
            <button class="icon-button" @click="open(row)"><View /></button>
            <button class="icon-button" @click="toggle(row)"><SwitchButton /></button>
            <button class="icon-button danger" @click="remove(row)"><Delete /></button>
          </div>
        </template>
      </el-table-column>
    </AdminTable>
    <el-drawer v-model="drawer" title="用户详情" size="360px">
      <el-descriptions v-if="current" :column="1" border>
        <el-descriptions-item label="用户名">{{ current.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ current.nickname }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ current.role }}</el-descriptions-item>
        <el-descriptions-item label="状态">{{ current.status }}</el-descriptions-item>
        <el-descriptions-item label="最近登录">{{ current.lastLoginTime || '—' }}</el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, SwitchButton, View } from '@element-plus/icons-vue'
import PageHeader from '@/components/common/PageHeader.vue'
import AdminTable from '@/components/admin/AdminTable.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { deleteAdminUser, getAdminUsers, updateUserStatus } from '@/api/admin'

const rows = ref([])
const keyword = ref('')
const role = ref('')
const status = ref('')
const page = ref(1)
const pageSize = 10
const total = ref(0)
const loading = ref(false)
const drawer = ref(false)
const current = ref(null)

async function load() {
  loading.value = true
  try {
    const res = await getAdminUsers({ keyword: keyword.value, role: role.value, status: status.value, page: page.value, pageSize })
    rows.value = res.data.list || []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}
function refresh() {
  page.value = 1
  load()
}
function onSearch(value) {
  keyword.value = value
  refresh()
}
function onPageChange(value) {
  page.value = value
  load()
}
function open(row) {
  current.value = row
  drawer.value = true
}
async function toggle(row) {
  const next = row.status === 'active' ? 'disabled' : 'active'
  await updateUserStatus(row.id, next)
  ElMessage.success('用户状态已更新')
  load()
}
async function remove(row) {
  await ElMessageBox.confirm(`确认删除用户 ${row.username}？`, '删除确认', { type: 'warning' })
  await deleteAdminUser(row.id)
  ElMessage.success('用户已删除')
  load()
}
onMounted(load)
</script>
