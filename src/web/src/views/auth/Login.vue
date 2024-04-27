<template>
  <div class="h-full login-bg bg-slate-50">
    <div class="flex h-full justify-center items-center">
      <div class="h-max min-w-[16rem] w-1/4 max-w-[24rem] text-center items-center">
        <div class="inline-flex mt-4 mb-8 items-center">
          <img src="@/assets/deloop.png" class="h-12 mr-2" />
          <h1 class="font-bold text-4xl font-mono" style="color: #092B2C;">Deloop</h1>
        </div>

        <div v-if="showLogin">
          <el-form ref="loginFormRef" :model="loginUser" size="large" :rules="rules" show-message>
            <el-form-item prop="name">
              <el-input v-model="loginUser.name" placeholder="email">
                <template #prefix>
                  <User />
                </template>
              </el-input>
            </el-form-item>

            <el-form-item prop="password">
              <el-input v-model="loginUser.password" type="password" placeholder="123456" show-password>
                <template #prefix>
                  <Lock />
                </template>
              </el-input>
            </el-form-item>
          </el-form>

          <el-button color="#092B2C" style="color: white" size="large" @click="signup(loginFormRef)">SIGN UP</el-button>
          <el-button color="#092B2C" style="color: white" size="large" @click="login(loginFormRef)">LOG IN</el-button>
        </div>

        <div v-if="showLogin == false">
          <el-form ref="registerFormRef" :model="registerUser" label-position="top" :rules="rules" label-width="auto"
            size="large">
            <el-form-item label="Username" prop="name">
              <el-input placeholder="user name" v-model="registerUser.name" size="large"></el-input>
            </el-form-item>
            <el-form-item label="Email" prop="email">
              <el-input placeholder="email" v-model="registerUser.email"></el-input>
            </el-form-item>
            <el-form-item label="Password" prop="password">
              <el-input placeholder="password" minlength="6" v-model="registerUser.password"></el-input>
            </el-form-item>
          </el-form>

          <!-- <el-button class="w-full" color="#092B2C" style="color: white" size="large" @click="register(registerFormRef)">SIGN UP</el-button> -->
          <div class="mt-[0.25rem] text-right">
            <el-button link @click="showLogin = true">SIGN IN</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-bg {
  background-image: url('@/assets/login-bg.svg');
  background-repeat: no-repeat;
  background-size: 100% auto;
  background-position: 0 100%;
}
</style>

<script setup>
import { ElMessage, ElNotification } from "element-plus"
import { User, Lock, Github, Wechat } from '@icon-park/vue-next'
import { ref, reactive } from 'vue'
import request from '@/axios'
import { useRouter } from 'vue-router'
import { setUser } from '@/utils';

const router = useRouter();

const loginFormRef = ref();
const registerFormRef = ref();

const showLogin = ref(true);

const loginUser = reactive({
  name: "alexwww123456@gmail.com",
  password: "wangLI420902",
});


const login = async (form) => {
  if (!form) {
    return
  }

  let name = loginUser.name;

  let success = function () {
    ElNotification.success({
      title: 'Login Success',
      message: 'Hi~ ' + name,
      showClose: true,
      duration: 1500,
    })
    router.push('/');
  }

  await form.validate((valid, fields) => {
    if (valid) {
      request.post("/api/v1/de/auth/token", {
        name: loginUser.name,
        password: loginUser.password,
        setCookie: true,
      }).then((response) => {
        success()

        setUser({
          id: 1,
          name: loginUser.name,
          avatar: "",
          authInfos: [],
        })

      })
    } else {
      console.log("input invaild", fields)
      ElMessage({
        message: "Input invalid" + fields,
        type: "error",
      });
    }
  });
};


const signup = async (form) => {
  if (!form) {
    return
  }

  await form.validate((valid, fields) => {
    if (valid) {
      request.post("/api/v1/de/auth/user", {
        name: loginUser.name,
        password: loginUser.password,
      }).then((response) => {
        if (response.status == 200) {
          ElMessage({
            message: 'Register success',
            type: 'success',
          })
          loginUser.name = registerUser.name;
          loginUser.password = registerUser.password;
        }
      }).catch((error) => {
        if (error.response.status == 409)
        {
          ElMessage({
            message: 'User has already signed up',
            type: 'error',
          })
        }
        else{
          ElMessage.error("Request Failure")
        }
      })
    } else {
      console.log("Input invalid =>", fields)
      ElMessage({
        message: "Input invalid",
        type: "error",
      });
    }
  });
};

</script>
