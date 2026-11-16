# Dev preview: runs the GTK apps and serves them to a browser (GTK Broadway)
FROM debian:bookworm-slim
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      python3 python3-gi gir1.2-gtk-3.0 libgtk-3-bin adwaita-icon-theme fonts-inter fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*
ENV PYTHONPATH=/app/src GDK_BACKEND=broadway BROADWAY_DISPLAY=:5
COPY run-app.sh /usr/local/bin/run-app
ENTRYPOINT ["run-app"]
