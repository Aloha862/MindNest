<template>
  <section class="tips">
    <h3>小贴士</h3>
    <p>拍摄时尽量保持光线均匀、字迹清晰</p>
    <p>倾斜或弯曲会自动通过预处理矫正</p>
    <p>多题图片会被拆分为多张题目卡片</p>
  </section>
</template>

<style scoped>
.tips {
  padding: 4px 18px;
  color: var(--sm-muted);
  line-height: 1.8;
}

h3 {
  color: var(--sm-text);
}

p {
  margin: 2px 0;
}

p::before {
  content: '• ';
}
</style>
