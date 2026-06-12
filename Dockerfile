# 使用 Ubuntu 22.04 作為基底
FROM ubuntu:22.04

# 安裝 SSH 伺服器
RUN apt-get update && apt-get install -y openssh-server sudo
RUN mkdir /var/run/sshd

# 設定 root 密碼為 'yocto' (僅供本地測試使用)
RUN echo 'root:yocto' | chpasswd

# 允許 root 透過密碼 SSH 登入
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# 建立假的 bitbake 執行檔 (Mock)
RUN echo '#!/bin/bash\n\
echo "Loading cache: 100%"\n\
sleep 1\n\
echo "Parsing recipes: 100%"\n\
echo "Executing Tasks..."\n\
sleep 3\n\
echo "Task do_rootfs: Succeeded"\n\
echo "Task do_image_wic: Succeeded"\n\
touch /root/Image-imx93.bin\n\
echo "Build successful. Image generated at /root/Image-imx93.bin"\n\
' > /usr/local/bin/bitbake

# 賦予執行權限
RUN chmod +x /usr/local/bin/bitbake

# 開放 22 埠
EXPOSE 22

# 啟動 SSH 服務
CMD ["/usr/sbin/sshd", "-D"]