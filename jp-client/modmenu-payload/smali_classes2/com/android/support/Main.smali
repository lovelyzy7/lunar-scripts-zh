.class public Lcom/android/support/Main;
.super Ljava/lang/Object;
.source "Main.java"


# direct methods
.method static constructor <clinit>()V
    .locals 1

    .line 18
    const-string v0, "niermenu"

    invoke-static {v0}, Ljava/lang/System;->loadLibrary(Ljava/lang/String;)V

    .line 19
    return-void
.end method

.method public constructor <init>()V
    .locals 0

    .line 12
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method private static native CheckOverlayPermission(Landroid/content/Context;)V
.end method

.method public static Start(Landroid/content/Context;)V
    .locals 1
    .param p0, "context"    # Landroid/content/Context;

    .line 36
    const/4 v0, 0x0

    invoke-static {p0, v0}, Lcom/android/support/CrashHandler;->init(Landroid/content/Context;Z)V

    .line 38
    invoke-static {p0}, Lcom/android/support/Main;->CheckOverlayPermission(Landroid/content/Context;)V

    .line 39
    return-void
.end method

.method public static StartWithoutPermission(Landroid/content/Context;)V
    .locals 2
    .param p0, "context"    # Landroid/content/Context;

    .line 24
    const/4 v0, 0x1

    invoke-static {p0, v0}, Lcom/android/support/CrashHandler;->init(Landroid/content/Context;Z)V

    .line 25
    instance-of v1, p0, Landroid/app/Activity;

    if-eqz v1, :cond_0

    .line 27
    new-instance v0, Lcom/android/support/Menu;

    invoke-direct {v0, p0}, Lcom/android/support/Menu;-><init>(Landroid/content/Context;)V

    .line 28
    .local v0, "menu":Lcom/android/support/Menu;
    invoke-virtual {v0}, Lcom/android/support/Menu;->SetWindowManagerActivity()V

    .line 29
    invoke-virtual {v0}, Lcom/android/support/Menu;->ShowMenu()V

    .line 30
    .end local v0    # "menu":Lcom/android/support/Menu;
    goto :goto_0

    .line 31
    :cond_0
    const-string v1, "Failed to launch the mod menu\n"

    invoke-static {p0, v1, v0}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;

    move-result-object v0

    invoke-virtual {v0}, Landroid/widget/Toast;->show()V

    .line 33
    :goto_0
    return-void
.end method
