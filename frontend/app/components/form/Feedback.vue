<script setup lang="ts">
import { object, string, mixed, boolean } from 'yup'
import type { InferType } from 'yup'
import type { FormSubmitEvent } from '@nuxt/ui'
import { vMaska } from 'maska/vue'
import getCurrentApiUrl from '~/helpers/getCurrentApiUrl'

// Типы обращений
const messageTypes = [
  { value: 'general', label: 'Общий вопрос' },
  { value: 'support', label: 'Техподдержка' },
  { value: 'sales', label: 'Отдел продаж' },
  { value: 'partnership', label: 'Партнерство' },
  { value: 'complaint', label: 'Жалоба' },
  { value: 'other', label: 'Другое' }
]

// Получаем конфигурацию формы (URL политики и т.д.)
const { data: config } = await useFetch('/api/feedback/config/', {
  baseURL: getCurrentApiUrl()
})

// Схема валидации
const schema = object({
  name: string().required('Обязательно для заполнения'),
  email: string().email('Неверный формат email').required('Обязательно для заполнения'),
  phone: string()
    .required('Обязательно для заполнения')
    .test('phone-format', 'Неверный формат телефона', (value) => {
      if (!value) return false
      const cleaned = value.replace(/\D/g, '')
      return cleaned.length >= 10 && cleaned.length <= 15
    }),
  message_type: string().required('Выберите тип обращения'),
  subject: string().optional(),
  message: string().required('Обязательно для заполнения').min(10, 'Минимум 10 символов'),
  privacy_policy_accepted: boolean()
    .oneOf([true], 'Вы должны принять политику конфиденциальности')
    .required('Обязательно для заполнения'),
  attachment: mixed<File>().optional().test('file-size', 'Размер файла не должен превышать 10MB', (value) => {
    if (!value) return true
    return value.size <= 10 * 1024 * 1024
  })
})

type Schema = InferType<typeof schema>

// Состояние формы
const state = reactive({
  name: '',
  email: '',
  phone: '',
  message_type: 'general',
  subject: '',
  message: '',
  privacy_policy_accepted: false,
  attachment: undefined as File | undefined
})

const fileInput = ref<HTMLInputElement | null>(null)
const isSubmitting = ref(false)
const submitError = ref('')

const toast = useToast()

// Обработка выбора файла
function onFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]

  if (file) {
    // Проверка типа файла
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
    if (!allowedTypes.includes(file.type)) {
      toast.add({
        title: 'Ошибка',
        description: 'Допустимые форматы: JPG, PNG, GIF, PDF',
        color: 'error'
      })
      if (fileInput.value) fileInput.value.value = ''
      return
    }

    // Проверка размера
    if (file.size > 10 * 1024 * 1024) {
      toast.add({
        title: 'Ошибка',
        description: 'Размер файла не должен превышать 10MB',
        color: 'error'
      })
      if (fileInput.value) fileInput.value.value = ''
      return
    }

    state.attachment = file
  }
}

// Удаление файла
function removeFile() {
  state.attachment = undefined
  if (fileInput.value) fileInput.value.value = ''
}

// Отправка формы
async function onSubmit(event: FormSubmitEvent<Schema>) {
  isSubmitting.value = true
  submitError.value = ''

  try {
    const formData = new FormData()

    // Добавляем все поля
    formData.append('name', event.data.name)
    formData.append('email', event.data.email)
    formData.append('phone', event.data.phone.replace(/\D/g, '')) // Чистый номер для бэка
    formData.append('message_type', event.data.message_type)
    formData.append('subject', event.data.subject || '')
    formData.append('message', event.data.message)
    formData.append('privacy_policy_accepted', 'true')

    // URL политики из настроек
    if (config.value?.privacy_policy_url) {
      formData.append('privacy_policy_url', config.value.privacy_policy_url)
    }

    // Файл если есть
    if (state.attachment) {
      formData.append('attachment', state.attachment)
    }

    // Отправка
    const { data, error } = await useFetch('/api/feedback/', {
      method: 'POST',
      body: formData,
      baseURL: getCurrentApiUrl()
    })

    if (error.value) {
      throw new Error(error.value.data?.error || 'Ошибка отправки')
    }

    // Успех
    toast.add({
      title: 'Успешно!',
      description: data.value?.message || 'Ваше сообщение отправлено. Мы свяжемся с вами в ближайшее время.',
      color: 'success',
      timeout: 5000
    })

    // Сброс формы
    resetForm()
  } catch (err: any) {
    submitError.value = err.message || 'Произошла ошибка при отправке'
    toast.add({
      title: 'Ошибка',
      description: submitError.value,
      color: 'error'
    })
  } finally {
    isSubmitting.value = false
  }
}

// Сброс формы
function resetForm() {
  state.name = ''
  state.email = ''
  state.phone = ''
  state.message_type = 'general'
  state.subject = ''
  state.message = ''
  state.privacy_policy_accepted = false
  state.attachment = undefined
  if (fileInput.value) fileInput.value.value = ''
}

// URL политики из настроек
const privacyPolicyUrl = computed(() => {
  return config.value?.privacy_policy_url || '/privacy'
})
</script>

<template>
  <UForm
    :schema="schema"
    :state="state"
    class="space-y-4 max-w-lg mx-auto"
    @submit="onSubmit"
  >
    <!-- Имя -->
    <UFormField
      label="Имя"
      name="name"
    >
      <UInput
        v-model="state.name"
        placeholder="Введите ваше имя"
        class="w-full"
      />
    </UFormField>

    <!-- Email -->
    <UFormField
      label="E-mail"
      name="email"
    >
      <UInput
        v-model="state.email"
        type="email"
        placeholder="example@mail.com"
        class="w-full"
      />
    </UFormField>

    <!-- Телефон -->
    <UFormField
      label="Телефон"
      name="phone"
    >
      <UInput
        v-model="state.phone"
        v-maska="'+7 (###) ###-##-##'"
        placeholder="+7 (999) 999-99-99"
        class="w-full"
      />
    </UFormField>

    <!-- Тип обращения -->
    <UFormField
      label="Тип обращения"
      name="message_type"
    >
      <USelectMenu
        v-model="state.message_type"
        :options="messageTypes"
        option-attribute="label"
        value-attribute="value"
        class="w-full"
      />
    </UFormField>

    <!-- Тема (опционально) -->
    <UFormField
      label="Тема"
      name="subject"
    >
      <UInput
        v-model="state.subject"
        placeholder="Кратко о чем ваш вопрос"
        class="w-full"
      />
    </UFormField>

    <!-- Сообщение -->
    <UFormField
      label="Сообщение"
      name="message"
    >
      <UTextarea
        v-model="state.message"
        placeholder="Подробно опишите ваш вопрос или проблему..."
        :rows="5"
        class="w-full"
      />
    </UFormField>

    <!-- Прикрепление файла -->
    <UFormField
      label="Прикрепить файл"
      name="attachment"
    >
      <div class="space-y-2">
        <input
          ref="fileInput"
          type="file"
          accept=".jpg,.jpeg,.png,.gif,.pdf"
          class="hidden"
          @change="onFileSelect"
        >

        <div
          v-if="!state.attachment"
          class="flex items-center gap-2"
        >
          <UButton
            type="button"
            color="gray"
            variant="soft"
            icon="i-heroicons-paper-clip"
            @click="fileInput?.click()"
          >
            Выбрать файл
          </UButton>
          <span class="text-sm text-gray-500">
            JPG, PNG, GIF, PDF до 10MB
          </span>
        </div>

        <div
          v-else
          class="flex items-center gap-2 p-3 bg-gray-50 rounded-lg"
        >
          <UIcon
            name="i-heroicons-document"
            class="text-gray-500"
          />
          <span class="text-sm truncate flex-1">{{ state.attachment.name }}</span>
          <span class="text-xs text-gray-500">
            {{ (state.attachment.size / 1024 / 1024).toFixed(2) }} MB
          </span>
          <UButton
            type="button"
            color="red"
            variant="ghost"
            size="xs"
            icon="i-heroicons-x-mark"
            @click="removeFile"
          />
        </div>
      </div>
    </UFormField>

    <!-- Политика конфиденциальности -->
    <UFormField name="privacy_policy_accepted">
      <UCheckbox v-model="state.privacy_policy_accepted">
        <template #label>
          <span class="text-sm">
            Я согласен на обработку персональных данных в соответствии с
            <NuxtLink
              :to="privacyPolicyUrl"
              target="_blank"
              class="text-primary-600 hover:underline"
            >
              политикой конфиденциальности
            </NuxtLink>
          </span>
        </template>
      </UCheckbox>
    </UFormField>

    <!-- Ошибка отправки -->
    <UAlert
      v-if="submitError"
      color="red"
      variant="soft"
      icon="i-heroicons-exclamation-triangle"
      :title="submitError"
    />

    <!-- Кнопка отправки -->
    <UButton
      type="submit"
      color="primary"
      size="lg"
      block
      :loading="isSubmitting"
      :disabled="isSubmitting"
    >
      <template v-if="isSubmitting">
        <UIcon
          name="i-heroicons-arrow-path"
          class="animate-spin mr-2"
        />
        Отправка...
      </template>
      <template v-else>
        Отправить сообщение
      </template>
    </UButton>
  </UForm>
</template>
