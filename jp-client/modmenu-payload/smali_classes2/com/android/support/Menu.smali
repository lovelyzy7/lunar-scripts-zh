.class public Lcom/android/support/Menu;
.super Ljava/lang/Object;
.source "Menu.java"


# static fields
.field public static final TAG:Ljava/lang/String; = "Mod_Menu"


# instance fields
.field BORDER_COLOR:I

.field BTN_COLOR:I

.field BtnOFF:I

.field BtnON:I

.field CARD_RADIUS:I

.field CHIP_BG:I

.field CategoryBG:I

.field CheckBoxColor:I

.field CollapseColor:I

.field CollapseSubColor:I

.field ICON_ALPHA:F

.field ICON_SIZE:I

.field INK:I

.field MENU_BG_COLOR:I

.field MENU_CORNER:F

.field MENU_FEATURE_BG_COLOR:I

.field MENU_HEIGHT:I

.field MENU_WIDTH:I

.field NumberTxtColor:Ljava/lang/String;

.field PANEL:I

.field PAPER:I

.field POS_X:I

.field POS_Y:I

.field RadioColor:I

.field STATUS_ALERT:I

.field STATUS_OK:I

.field SeekBarColor:I

.field SeekBarProgressColor:I

.field TEXT_COLOR:I

.field TEXT_COLOR_2:I

.field TRACKING:F

.field ToggleOFF:I

.field ToggleON:I

.field getContext:Landroid/content/Context;

.field mCollapse:Landroid/widget/LinearLayout;

.field mCollapsed:Landroid/widget/RelativeLayout;

.field mExpanded:Landroid/widget/LinearLayout;

.field mRootContainer:Landroid/widget/RelativeLayout;

.field mSettings:Landroid/widget/LinearLayout;

.field mSubTitle:Landroid/widget/TextView;

.field mTitle:Landroid/widget/TextView;

.field mWindowManager:Landroid/view/WindowManager;

.field mods:Landroid/widget/LinearLayout;

.field overlayRequired:Z

.field rootFrame:Landroid/widget/FrameLayout;

.field scrlLL:Landroid/widget/LinearLayout$LayoutParams;

.field scrlLLExpanded:Landroid/widget/LinearLayout$LayoutParams;

.field scrollView:Landroid/widget/ScrollView;

.field startimage:Landroid/widget/ImageView;

.field stopChecking:Z

.field private uiScale:F

.field vmParams:Landroid/view/WindowManager$LayoutParams;


# direct methods
.method public constructor <init>(Landroid/content/Context;)V
    .locals 22
    .param p1, "context"    # Landroid/content/Context;

    .line 154
    move-object/from16 v0, p0

    move-object/from16 v1, p1

    invoke-direct/range {p0 .. p0}, Ljava/lang/Object;-><init>()V

    .line 76
    const-string v2, "#2C2922"

    invoke-static {v2}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v3

    iput v3, v0, Lcom/android/support/Menu;->TEXT_COLOR:I

    .line 77
    invoke-static {v2}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v2

    iput v2, v0, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    .line 78
    const-string v2, "#D8D1BB"

    invoke-static {v2}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v2

    iput v2, v0, Lcom/android/support/Menu;->BTN_COLOR:I

    .line 79
    const-string v2, "#F2CFC7B0"

    invoke-static {v2}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v2

    iput v2, v0, Lcom/android/support/Menu;->MENU_BG_COLOR:I

    .line 80
    const-string v2, "#E8D8D1BB"

    invoke-static {v2}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v2

    iput v2, v0, Lcom/android/support/Menu;->MENU_FEATURE_BG_COLOR:I

    .line 82
    const/high16 v2, 0x3f800000    # 1.0f

    iput v2, v0, Lcom/android/support/Menu;->uiScale:F

    .line 95
    const/16 v3, 0x122

    iput v3, v0, Lcom/android/support/Menu;->MENU_WIDTH:I

    .line 96
    const/16 v3, 0xd2

    iput v3, v0, Lcom/android/support/Menu;->MENU_HEIGHT:I

    .line 97
    const/4 v3, 0x0

    iput v3, v0, Lcom/android/support/Menu;->POS_X:I

    .line 98
    const/16 v4, 0x64

    iput v4, v0, Lcom/android/support/Menu;->POS_Y:I

    .line 100
    const/high16 v4, 0x40000000    # 2.0f

    iput v4, v0, Lcom/android/support/Menu;->MENU_CORNER:F

    .line 101
    const/16 v4, 0x2d

    iput v4, v0, Lcom/android/support/Menu;->ICON_SIZE:I

    .line 102
    const v4, 0x3f333333    # 0.7f

    iput v4, v0, Lcom/android/support/Menu;->ICON_ALPHA:F

    .line 103
    const-string v4, "#3A4D24"

    invoke-static {v4}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v5

    iput v5, v0, Lcom/android/support/Menu;->ToggleON:I

    .line 104
    const-string v5, "#6B0A0A"

    invoke-static {v5}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v6

    iput v6, v0, Lcom/android/support/Menu;->ToggleOFF:I

    .line 105
    invoke-static {v4}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v4

    iput v4, v0, Lcom/android/support/Menu;->BtnON:I

    .line 106
    invoke-static {v5}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v4

    iput v4, v0, Lcom/android/support/Menu;->BtnOFF:I

    .line 108
    const-string v4, "#D3CEB8"

    invoke-static {v4}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v4

    iput v4, v0, Lcom/android/support/Menu;->PAPER:I

    .line 109
    const-string v4, "#D8D3BD"

    invoke-static {v4}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v4

    iput v4, v0, Lcom/android/support/Menu;->PANEL:I

    .line 110
    const-string v4, "#3A372F"

    invoke-static {v4}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v4

    iput v4, v0, Lcom/android/support/Menu;->INK:I

    .line 111
    const-string v4, "#BCB69E"

    invoke-static {v4}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v4

    iput v4, v0, Lcom/android/support/Menu;->CHIP_BG:I

    .line 112
    const-string v4, "#6E7356"

    invoke-static {v4}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v4

    iput v4, v0, Lcom/android/support/Menu;->STATUS_OK:I

    .line 113
    const-string v4, "#7A1C14"

    invoke-static {v4}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v4

    iput v4, v0, Lcom/android/support/Menu;->STATUS_ALERT:I

    .line 114
    const v4, 0x3e23d70a    # 0.16f

    iput v4, v0, Lcom/android/support/Menu;->TRACKING:F

    .line 115
    const/16 v4, 0x8

    iput v4, v0, Lcom/android/support/Menu;->CARD_RADIUS:I

    .line 116
    const-string v6, "#1A1814"

    invoke-static {v6}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v7

    iput v7, v0, Lcom/android/support/Menu;->CategoryBG:I

    .line 117
    invoke-static {v6}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v7

    iput v7, v0, Lcom/android/support/Menu;->SeekBarColor:I

    .line 118
    invoke-static {v6}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v7

    iput v7, v0, Lcom/android/support/Menu;->SeekBarProgressColor:I

    .line 119
    invoke-static {v6}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v7

    iput v7, v0, Lcom/android/support/Menu;->CheckBoxColor:I

    .line 120
    invoke-static {v6}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v7

    iput v7, v0, Lcom/android/support/Menu;->RadioColor:I

    .line 121
    const-string v7, "#B8B099"

    invoke-static {v7}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v7

    iput v7, v0, Lcom/android/support/Menu;->CollapseColor:I

    .line 122
    const-string v7, "#C9C1AA"

    invoke-static {v7}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v7

    iput v7, v0, Lcom/android/support/Menu;->CollapseSubColor:I

    .line 123
    invoke-static {v6}, Landroid/graphics/Color;->parseColor(Ljava/lang/String;)I

    move-result v6

    iput v6, v0, Lcom/android/support/Menu;->BORDER_COLOR:I

    .line 124
    iput-object v5, v0, Lcom/android/support/Menu;->NumberTxtColor:Ljava/lang/String;

    .line 156
    iput-object v1, v0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    .line 157
    sput-object v1, Lcom/android/support/Preferences;->context:Landroid/content/Context;

    .line 158
    new-instance v5, Landroid/widget/FrameLayout;

    invoke-direct {v5, v1}, Landroid/widget/FrameLayout;-><init>(Landroid/content/Context;)V

    iput-object v5, v0, Lcom/android/support/Menu;->rootFrame:Landroid/widget/FrameLayout;

    .line 159
    iget-object v5, v0, Lcom/android/support/Menu;->rootFrame:Landroid/widget/FrameLayout;

    invoke-direct/range {p0 .. p0}, Lcom/android/support/Menu;->onTouchListener()Landroid/view/View$OnTouchListener;

    move-result-object v6

    invoke-virtual {v5, v6}, Landroid/widget/FrameLayout;->setOnTouchListener(Landroid/view/View$OnTouchListener;)V

    .line 160
    new-instance v5, Landroid/widget/RelativeLayout;

    invoke-direct {v5, v1}, Landroid/widget/RelativeLayout;-><init>(Landroid/content/Context;)V

    iput-object v5, v0, Lcom/android/support/Menu;->mRootContainer:Landroid/widget/RelativeLayout;

    .line 161
    new-instance v5, Landroid/widget/RelativeLayout;

    invoke-direct {v5, v1}, Landroid/widget/RelativeLayout;-><init>(Landroid/content/Context;)V

    iput-object v5, v0, Lcom/android/support/Menu;->mCollapsed:Landroid/widget/RelativeLayout;

    .line 162
    iget-object v5, v0, Lcom/android/support/Menu;->mCollapsed:Landroid/widget/RelativeLayout;

    invoke-virtual {v5, v3}, Landroid/widget/RelativeLayout;->setVisibility(I)V

    .line 163
    iget-object v5, v0, Lcom/android/support/Menu;->mCollapsed:Landroid/widget/RelativeLayout;

    iget v6, v0, Lcom/android/support/Menu;->ICON_ALPHA:F

    invoke-virtual {v5, v6}, Landroid/widget/RelativeLayout;->setAlpha(F)V

    .line 166
    new-instance v5, Landroid/widget/LinearLayout;

    invoke-direct {v5, v1}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    iput-object v5, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    .line 167
    iget-object v5, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    invoke-virtual {v5, v4}, Landroid/widget/LinearLayout;->setVisibility(I)V

    .line 168
    iget-object v4, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    iget v5, v0, Lcom/android/support/Menu;->MENU_BG_COLOR:I

    invoke-virtual {v4, v5}, Landroid/widget/LinearLayout;->setBackgroundColor(I)V

    .line 169
    iget-object v4, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    const/4 v5, 0x1

    invoke-virtual {v4, v5}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 171
    iget-object v4, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    new-instance v6, Landroid/widget/LinearLayout$LayoutParams;

    iget v7, v0, Lcom/android/support/Menu;->MENU_WIDTH:I

    invoke-direct {v0, v7}, Lcom/android/support/Menu;->dp(I)I

    move-result v7

    const/4 v8, -0x2

    invoke-direct {v6, v7, v8}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    invoke-virtual {v4, v6}, Landroid/widget/LinearLayout;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 172
    new-instance v4, Landroid/graphics/drawable/GradientDrawable;

    invoke-direct {v4}, Landroid/graphics/drawable/GradientDrawable;-><init>()V

    .line 173
    .local v4, "gdMenuBody":Landroid/graphics/drawable/GradientDrawable;
    iget v6, v0, Lcom/android/support/Menu;->CARD_RADIUS:I

    invoke-direct {v0, v6}, Lcom/android/support/Menu;->dp(I)I

    move-result v6

    int-to-float v6, v6

    invoke-virtual {v4, v6}, Landroid/graphics/drawable/GradientDrawable;->setCornerRadius(F)V

    .line 174
    iget v6, v0, Lcom/android/support/Menu;->MENU_BG_COLOR:I

    invoke-virtual {v4, v6}, Landroid/graphics/drawable/GradientDrawable;->setColor(I)V

    .line 175
    const/4 v6, 0x2

    invoke-direct {v0, v6}, Lcom/android/support/Menu;->dp(I)I

    move-result v7

    iget v9, v0, Lcom/android/support/Menu;->BORDER_COLOR:I

    invoke-virtual {v4, v7, v9}, Landroid/graphics/drawable/GradientDrawable;->setStroke(II)V

    .line 176
    iget-object v7, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    invoke-virtual {v7, v4}, Landroid/widget/LinearLayout;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 179
    new-instance v7, Landroid/widget/ImageView;

    invoke-direct {v7, v1}, Landroid/widget/ImageView;-><init>(Landroid/content/Context;)V

    iput-object v7, v0, Lcom/android/support/Menu;->startimage:Landroid/widget/ImageView;

    .line 180
    iget-object v7, v0, Lcom/android/support/Menu;->startimage:Landroid/widget/ImageView;

    new-instance v9, Landroid/widget/RelativeLayout$LayoutParams;

    invoke-direct {v9, v8, v8}, Landroid/widget/RelativeLayout$LayoutParams;-><init>(II)V

    invoke-virtual {v7, v9}, Landroid/widget/ImageView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 181
    iget v7, v0, Lcom/android/support/Menu;->ICON_SIZE:I

    int-to-float v7, v7

    invoke-virtual/range {p1 .. p1}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    move-result-object v9

    invoke-virtual {v9}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    move-result-object v9

    invoke-static {v5, v7, v9}, Landroid/util/TypedValue;->applyDimension(IFLandroid/util/DisplayMetrics;)F

    move-result v7

    float-to-int v7, v7

    .line 182
    .local v7, "applyDimension":I
    iget-object v9, v0, Lcom/android/support/Menu;->startimage:Landroid/widget/ImageView;

    invoke-virtual {v9}, Landroid/widget/ImageView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v9

    iput v7, v9, Landroid/view/ViewGroup$LayoutParams;->height:I

    .line 183
    iget-object v9, v0, Lcom/android/support/Menu;->startimage:Landroid/widget/ImageView;

    invoke-virtual {v9}, Landroid/widget/ImageView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v9

    iput v7, v9, Landroid/view/ViewGroup$LayoutParams;->width:I

    .line 185
    iget-object v9, v0, Lcom/android/support/Menu;->startimage:Landroid/widget/ImageView;

    sget-object v10, Landroid/widget/ImageView$ScaleType;->FIT_XY:Landroid/widget/ImageView$ScaleType;

    invoke-virtual {v9, v10}, Landroid/widget/ImageView;->setScaleType(Landroid/widget/ImageView$ScaleType;)V

    .line 186
    invoke-virtual/range {p0 .. p0}, Lcom/android/support/Menu;->Icon()Ljava/lang/String;

    move-result-object v9

    invoke-static {v9, v3}, Landroid/util/Base64;->decode(Ljava/lang/String;I)[B

    move-result-object v9

    .line 187
    .local v9, "decode":[B
    iget-object v10, v0, Lcom/android/support/Menu;->startimage:Landroid/widget/ImageView;

    array-length v11, v9

    invoke-static {v9, v3, v11}, Landroid/graphics/BitmapFactory;->decodeByteArray([BII)Landroid/graphics/Bitmap;

    move-result-object v11

    invoke-virtual {v10, v11}, Landroid/widget/ImageView;->setImageBitmap(Landroid/graphics/Bitmap;)V

    .line 188
    iget-object v10, v0, Lcom/android/support/Menu;->startimage:Landroid/widget/ImageView;

    invoke-virtual {v10}, Landroid/widget/ImageView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v10

    check-cast v10, Landroid/view/ViewGroup$MarginLayoutParams;

    const/16 v11, 0xa

    invoke-direct {v0, v11}, Lcom/android/support/Menu;->convertDipToPixels(I)I

    move-result v12

    iput v12, v10, Landroid/view/ViewGroup$MarginLayoutParams;->topMargin:I

    .line 190
    iget-object v10, v0, Lcom/android/support/Menu;->startimage:Landroid/widget/ImageView;

    invoke-direct/range {p0 .. p0}, Lcom/android/support/Menu;->onTouchListener()Landroid/view/View$OnTouchListener;

    move-result-object v12

    invoke-virtual {v10, v12}, Landroid/widget/ImageView;->setOnTouchListener(Landroid/view/View$OnTouchListener;)V

    .line 191
    iget-object v10, v0, Lcom/android/support/Menu;->startimage:Landroid/widget/ImageView;

    new-instance v12, Lcom/android/support/Menu$1;

    invoke-direct {v12, v0}, Lcom/android/support/Menu$1;-><init>(Lcom/android/support/Menu;)V

    invoke-virtual {v10, v12}, Landroid/widget/ImageView;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 199
    new-instance v10, Landroid/webkit/WebView;

    invoke-direct {v10, v1}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V

    .line 200
    .local v10, "wView":Landroid/webkit/WebView;
    new-instance v12, Landroid/widget/RelativeLayout$LayoutParams;

    invoke-direct {v12, v8, v8}, Landroid/widget/RelativeLayout$LayoutParams;-><init>(II)V

    invoke-virtual {v10, v12}, Landroid/webkit/WebView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 201
    iget v12, v0, Lcom/android/support/Menu;->ICON_SIZE:I

    int-to-float v12, v12

    invoke-virtual/range {p1 .. p1}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    move-result-object v13

    invoke-virtual {v13}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    move-result-object v13

    invoke-static {v5, v12, v13}, Landroid/util/TypedValue;->applyDimension(IFLandroid/util/DisplayMetrics;)F

    move-result v12

    float-to-int v12, v12

    .line 202
    .local v12, "applyDimension2":I
    invoke-virtual {v10}, Landroid/webkit/WebView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v13

    iput v12, v13, Landroid/view/ViewGroup$LayoutParams;->height:I

    .line 203
    invoke-virtual {v10}, Landroid/webkit/WebView;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v13

    iput v12, v13, Landroid/view/ViewGroup$LayoutParams;->width:I

    .line 204
    new-instance v13, Ljava/lang/StringBuilder;

    invoke-direct {v13}, Ljava/lang/StringBuilder;-><init>()V

    const-string v14, "<html><head></head><body style=\"margin: 0; padding: 0\"><img src=\""

    invoke-virtual {v13, v14}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v13

    .line 207
    invoke-virtual/range {p0 .. p0}, Lcom/android/support/Menu;->IconWebViewData()Ljava/lang/String;

    move-result-object v14

    invoke-virtual {v13, v14}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v13

    const-string v14, "\" width=\""

    invoke-virtual {v13, v14}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v13

    iget v14, v0, Lcom/android/support/Menu;->ICON_SIZE:I

    invoke-virtual {v13, v14}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v13

    const-string v14, "\" height=\""

    invoke-virtual {v13, v14}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v13

    iget v14, v0, Lcom/android/support/Menu;->ICON_SIZE:I

    invoke-virtual {v13, v14}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v13

    const-string v14, "\" ></body></html>"

    invoke-virtual {v13, v14}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v13

    invoke-virtual {v13}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v13

    .line 204
    const-string v14, "text/html"

    const-string v15, "utf-8"

    invoke-virtual {v10, v13, v14, v15}, Landroid/webkit/WebView;->loadData(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V

    .line 210
    invoke-virtual {v10, v3}, Landroid/webkit/WebView;->setBackgroundColor(I)V

    .line 211
    iget v13, v0, Lcom/android/support/Menu;->ICON_ALPHA:F

    invoke-virtual {v10, v13}, Landroid/webkit/WebView;->setAlpha(F)V

    .line 212
    invoke-virtual {v10}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;

    move-result-object v13

    invoke-virtual {v13, v6}, Landroid/webkit/WebSettings;->setCacheMode(I)V

    .line 213
    invoke-direct/range {p0 .. p0}, Lcom/android/support/Menu;->onTouchListener()Landroid/view/View$OnTouchListener;

    move-result-object v13

    invoke-virtual {v10, v13}, Landroid/webkit/WebView;->setOnTouchListener(Landroid/view/View$OnTouchListener;)V

    .line 216
    new-instance v13, Landroid/widget/TextView;

    invoke-direct {v13, v1}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 217
    .local v13, "settings":Landroid/widget/TextView;
    sget v14, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v15, 0x17

    if-lt v14, v15, :cond_0

    const-string v14, "\u2699"

    goto :goto_0

    :cond_0
    const-string v14, "\ud83d\udd27"

    :goto_0
    invoke-virtual {v13, v14}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 218
    iget v14, v0, Lcom/android/support/Menu;->TEXT_COLOR:I

    invoke-virtual {v13, v14}, Landroid/widget/TextView;->setTextColor(I)V

    .line 219
    sget-object v14, Landroid/graphics/Typeface;->DEFAULT_BOLD:Landroid/graphics/Typeface;

    invoke-virtual {v13, v14}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;)V

    .line 220
    const/high16 v14, 0x41a00000    # 20.0f

    invoke-direct {v0, v13, v14}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 221
    new-instance v14, Landroid/widget/RelativeLayout$LayoutParams;

    invoke-direct {v14, v8, v8}, Landroid/widget/RelativeLayout$LayoutParams;-><init>(II)V

    .line 222
    .local v14, "rlsettings":Landroid/widget/RelativeLayout$LayoutParams;
    const/16 v15, 0xb

    invoke-virtual {v14, v15}, Landroid/widget/RelativeLayout$LayoutParams;->addRule(I)V

    .line 223
    invoke-virtual {v13, v14}, Landroid/widget/TextView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 224
    new-instance v15, Lcom/android/support/Menu$2;

    invoke-direct {v15, v0}, Lcom/android/support/Menu$2;-><init>(Lcom/android/support/Menu;)V

    invoke-virtual {v13, v15}, Landroid/widget/TextView;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 245
    new-instance v15, Landroid/widget/LinearLayout;

    invoke-direct {v15, v1}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    iput-object v15, v0, Lcom/android/support/Menu;->mSettings:Landroid/widget/LinearLayout;

    .line 246
    iget-object v15, v0, Lcom/android/support/Menu;->mSettings:Landroid/widget/LinearLayout;

    invoke-virtual {v15, v5}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 247
    invoke-virtual/range {p0 .. p0}, Lcom/android/support/Menu;->SettingsList()[Ljava/lang/String;

    move-result-object v15

    iget-object v2, v0, Lcom/android/support/Menu;->mSettings:Landroid/widget/LinearLayout;

    invoke-direct {v0, v15, v2}, Lcom/android/support/Menu;->featureList([Ljava/lang/String;Landroid/widget/LinearLayout;)V

    .line 250
    new-instance v2, Landroid/widget/RelativeLayout;

    invoke-direct {v2, v1}, Landroid/widget/RelativeLayout;-><init>(Landroid/content/Context;)V

    .line 251
    .local v2, "titleText":Landroid/widget/RelativeLayout;
    invoke-direct {v0, v11}, Lcom/android/support/Menu;->dp(I)I

    move-result v15

    const/4 v3, 0x6

    invoke-direct {v0, v3}, Lcom/android/support/Menu;->dp(I)I

    move-result v6

    invoke-direct {v0, v11}, Lcom/android/support/Menu;->dp(I)I

    move-result v8

    invoke-direct {v0, v3}, Lcom/android/support/Menu;->dp(I)I

    move-result v11

    invoke-virtual {v2, v15, v6, v8, v11}, Landroid/widget/RelativeLayout;->setPadding(IIII)V

    .line 252
    const/16 v6, 0x10

    invoke-virtual {v2, v6}, Landroid/widget/RelativeLayout;->setVerticalGravity(I)V

    .line 255
    new-instance v6, Landroid/widget/TextView;

    invoke-direct {v6, v1}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 256
    .local v6, "eyebrow":Landroid/widget/TextView;
    const-string v8, "BUNKER // POD 042"

    invoke-virtual {v6, v8}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 257
    iget v8, v0, Lcom/android/support/Menu;->INK:I

    invoke-virtual {v6, v8}, Landroid/widget/TextView;->setTextColor(I)V

    .line 258
    const v8, 0x3f3851ec    # 0.72f

    invoke-virtual {v6, v8}, Landroid/widget/TextView;->setAlpha(F)V

    .line 259
    sget-object v11, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v6, v11, v5}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    .line 260
    invoke-virtual {v6, v5}, Landroid/widget/TextView;->setAllCaps(Z)V

    .line 261
    invoke-direct {v0, v6}, Lcom/android/support/Menu;->track(Landroid/widget/TextView;)V

    .line 262
    const/high16 v11, 0x41100000    # 9.0f

    invoke-direct {v0, v6, v11}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 263
    const/16 v11, 0x11

    invoke-virtual {v6, v11}, Landroid/widget/TextView;->setGravity(I)V

    .line 264
    invoke-static {}, Landroid/view/View;->generateViewId()I

    move-result v15

    invoke-virtual {v6, v15}, Landroid/widget/TextView;->setId(I)V

    .line 265
    new-instance v15, Landroid/widget/RelativeLayout$LayoutParams;

    const/4 v3, -0x2

    invoke-direct {v15, v3, v3}, Landroid/widget/RelativeLayout$LayoutParams;-><init>(II)V

    move-object v3, v15

    .line 266
    .local v3, "rlEyebrow":Landroid/widget/RelativeLayout$LayoutParams;
    const/16 v15, 0xe

    invoke-virtual {v3, v15}, Landroid/widget/RelativeLayout$LayoutParams;->addRule(I)V

    .line 267
    const/16 v8, 0xa

    invoke-virtual {v3, v8}, Landroid/widget/RelativeLayout$LayoutParams;->addRule(I)V

    .line 268
    invoke-virtual {v6, v3}, Landroid/widget/TextView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 270
    new-instance v8, Landroid/widget/TextView;

    invoke-direct {v8, v1}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 271
    .local v8, "title":Landroid/widget/TextView;
    iget v15, v0, Lcom/android/support/Menu;->INK:I

    invoke-virtual {v8, v15}, Landroid/widget/TextView;->setTextColor(I)V

    .line 272
    sget-object v15, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v8, v15, v5}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    .line 273
    invoke-virtual {v8, v5}, Landroid/widget/TextView;->setAllCaps(Z)V

    .line 274
    invoke-direct {v0, v8}, Lcom/android/support/Menu;->track(Landroid/widget/TextView;)V

    .line 275
    const/high16 v15, 0x41880000    # 17.0f

    invoke-direct {v0, v8, v15}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 276
    invoke-virtual {v8, v11}, Landroid/widget/TextView;->setGravity(I)V

    .line 277
    new-instance v15, Landroid/widget/RelativeLayout$LayoutParams;

    const/4 v11, -0x2

    invoke-direct {v15, v11, v11}, Landroid/widget/RelativeLayout$LayoutParams;-><init>(II)V

    move-object v11, v15

    .line 278
    .local v11, "rl":Landroid/widget/RelativeLayout$LayoutParams;
    const/16 v15, 0xe

    invoke-virtual {v11, v15}, Landroid/widget/RelativeLayout$LayoutParams;->addRule(I)V

    .line 279
    invoke-virtual {v6}, Landroid/widget/TextView;->getId()I

    move-result v15

    const/4 v5, 0x3

    invoke-virtual {v11, v5, v15}, Landroid/widget/RelativeLayout$LayoutParams;->addRule(II)V

    .line 280
    invoke-virtual {v8, v11}, Landroid/widget/TextView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 283
    new-instance v15, Landroid/widget/TextView;

    invoke-direct {v15, v1}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 284
    .local v15, "subTitle":Landroid/widget/TextView;
    sget-object v5, Landroid/text/TextUtils$TruncateAt;->END:Landroid/text/TextUtils$TruncateAt;

    invoke-virtual {v15, v5}, Landroid/widget/TextView;->setEllipsize(Landroid/text/TextUtils$TruncateAt;)V

    .line 285
    const/4 v5, 0x1

    invoke-virtual {v15, v5}, Landroid/widget/TextView;->setSingleLine(Z)V

    .line 286
    iget v5, v0, Lcom/android/support/Menu;->INK:I

    invoke-virtual {v15, v5}, Landroid/widget/TextView;->setTextColor(I)V

    .line 287
    const v5, 0x3f3851ec    # 0.72f

    invoke-virtual {v15, v5}, Landroid/widget/TextView;->setAlpha(F)V

    .line 288
    sget-object v5, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v15, v5}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;)V

    .line 289
    invoke-direct {v0, v15}, Lcom/android/support/Menu;->track(Landroid/widget/TextView;)V

    .line 290
    const/high16 v5, 0x41200000    # 10.0f

    invoke-direct {v0, v15, v5}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 291
    const/16 v5, 0x11

    invoke-virtual {v15, v5}, Landroid/widget/TextView;->setGravity(I)V

    .line 292
    const/4 v5, 0x2

    invoke-direct {v0, v5}, Lcom/android/support/Menu;->dp(I)I

    move-result v5

    move-object/from16 v19, v3

    const/4 v3, 0x6

    .end local v3    # "rlEyebrow":Landroid/widget/RelativeLayout$LayoutParams;
    .local v19, "rlEyebrow":Landroid/widget/RelativeLayout$LayoutParams;
    invoke-direct {v0, v3}, Lcom/android/support/Menu;->dp(I)I

    move-result v3

    move-object/from16 v21, v4

    const/4 v4, 0x0

    .end local v4    # "gdMenuBody":Landroid/graphics/drawable/GradientDrawable;
    .local v21, "gdMenuBody":Landroid/graphics/drawable/GradientDrawable;
    invoke-virtual {v15, v4, v5, v4, v3}, Landroid/widget/TextView;->setPadding(IIII)V

    .line 295
    new-instance v3, Landroid/widget/ScrollView;

    invoke-direct {v3, v1}, Landroid/widget/ScrollView;-><init>(Landroid/content/Context;)V

    iput-object v3, v0, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    .line 297
    new-instance v3, Landroid/widget/LinearLayout$LayoutParams;

    iget v4, v0, Lcom/android/support/Menu;->MENU_HEIGHT:I

    invoke-direct {v0, v4}, Lcom/android/support/Menu;->dp(I)I

    move-result v4

    const/4 v5, -0x1

    invoke-direct {v3, v5, v4}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    iput-object v3, v0, Lcom/android/support/Menu;->scrlLL:Landroid/widget/LinearLayout$LayoutParams;

    .line 298
    new-instance v3, Landroid/widget/LinearLayout$LayoutParams;

    iget-object v4, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    invoke-virtual {v4}, Landroid/widget/LinearLayout;->getLayoutParams()Landroid/view/ViewGroup$LayoutParams;

    move-result-object v4

    invoke-direct {v3, v4}, Landroid/widget/LinearLayout$LayoutParams;-><init>(Landroid/view/ViewGroup$LayoutParams;)V

    iput-object v3, v0, Lcom/android/support/Menu;->scrlLLExpanded:Landroid/widget/LinearLayout$LayoutParams;

    .line 299
    iget-object v3, v0, Lcom/android/support/Menu;->scrlLLExpanded:Landroid/widget/LinearLayout$LayoutParams;

    const/high16 v4, 0x3f800000    # 1.0f

    iput v4, v3, Landroid/widget/LinearLayout$LayoutParams;->weight:F

    .line 300
    iget-object v3, v0, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    sget-boolean v4, Lcom/android/support/Preferences;->isExpanded:Z

    if-eqz v4, :cond_1

    iget-object v4, v0, Lcom/android/support/Menu;->scrlLLExpanded:Landroid/widget/LinearLayout$LayoutParams;

    goto :goto_1

    :cond_1
    iget-object v4, v0, Lcom/android/support/Menu;->scrlLL:Landroid/widget/LinearLayout$LayoutParams;

    :goto_1
    invoke-virtual {v3, v4}, Landroid/widget/ScrollView;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 301
    iget-object v3, v0, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    iget v4, v0, Lcom/android/support/Menu;->MENU_FEATURE_BG_COLOR:I

    invoke-virtual {v3, v4}, Landroid/widget/ScrollView;->setBackgroundColor(I)V

    .line 302
    new-instance v3, Landroid/widget/LinearLayout;

    invoke-direct {v3, v1}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    iput-object v3, v0, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    .line 303
    iget-object v3, v0, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    const/4 v4, 0x1

    invoke-virtual {v3, v4}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 306
    new-instance v3, Landroid/widget/RelativeLayout;

    invoke-direct {v3, v1}, Landroid/widget/RelativeLayout;-><init>(Landroid/content/Context;)V

    .line 307
    .local v3, "relativeLayout":Landroid/widget/RelativeLayout;
    const/4 v4, 0x3

    const/16 v5, 0xa

    invoke-virtual {v3, v5, v4, v5, v4}, Landroid/widget/RelativeLayout;->setPadding(IIII)V

    .line 308
    const/16 v4, 0x11

    invoke-virtual {v3, v4}, Landroid/widget/RelativeLayout;->setVerticalGravity(I)V

    .line 311
    new-instance v4, Landroid/widget/RelativeLayout$LayoutParams;

    const/4 v5, -0x2

    invoke-direct {v4, v5, v5}, Landroid/widget/RelativeLayout$LayoutParams;-><init>(II)V

    .line 312
    .local v4, "lParamsHideBtn":Landroid/widget/RelativeLayout$LayoutParams;
    const/16 v5, 0x9

    invoke-virtual {v4, v5}, Landroid/widget/RelativeLayout$LayoutParams;->addRule(I)V

    .line 314
    new-instance v5, Landroid/widget/Button;

    invoke-direct {v5, v1}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    .line 315
    .local v5, "hideBtn":Landroid/widget/Button;
    invoke-virtual {v5, v4}, Landroid/widget/Button;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 316
    move-object/from16 v17, v4

    const/4 v4, 0x0

    .end local v4    # "lParamsHideBtn":Landroid/widget/RelativeLayout$LayoutParams;
    .local v17, "lParamsHideBtn":Landroid/widget/RelativeLayout$LayoutParams;
    invoke-virtual {v5, v4}, Landroid/widget/Button;->setBackgroundColor(I)V

    .line 317
    const-string v4, "HIDE/KILL (Hold)"

    invoke-virtual {v5, v4}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 318
    iget v4, v0, Lcom/android/support/Menu;->TEXT_COLOR:I

    invoke-virtual {v5, v4}, Landroid/widget/Button;->setTextColor(I)V

    .line 319
    new-instance v4, Lcom/android/support/Menu$3;

    invoke-direct {v4, v0}, Lcom/android/support/Menu$3;-><init>(Lcom/android/support/Menu;)V

    invoke-virtual {v5, v4}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 327
    new-instance v4, Lcom/android/support/Menu$4;

    invoke-direct {v4, v0}, Lcom/android/support/Menu$4;-><init>(Lcom/android/support/Menu;)V

    invoke-virtual {v5, v4}, Landroid/widget/Button;->setOnLongClickListener(Landroid/view/View$OnLongClickListener;)V

    .line 337
    new-instance v4, Landroid/widget/RelativeLayout$LayoutParams;

    move/from16 v20, v7

    const/4 v7, -0x2

    .end local v7    # "applyDimension":I
    .local v20, "applyDimension":I
    invoke-direct {v4, v7, v7}, Landroid/widget/RelativeLayout$LayoutParams;-><init>(II)V

    .line 338
    .local v4, "lParamsCloseBtn":Landroid/widget/RelativeLayout$LayoutParams;
    const/16 v7, 0xb

    invoke-virtual {v4, v7}, Landroid/widget/RelativeLayout$LayoutParams;->addRule(I)V

    .line 340
    new-instance v7, Landroid/widget/Button;

    invoke-direct {v7, v1}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    .line 341
    .local v7, "closeBtn":Landroid/widget/Button;
    invoke-virtual {v7, v4}, Landroid/widget/Button;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 342
    move-object/from16 v16, v4

    const/4 v4, 0x0

    .end local v4    # "lParamsCloseBtn":Landroid/widget/RelativeLayout$LayoutParams;
    .local v16, "lParamsCloseBtn":Landroid/widget/RelativeLayout$LayoutParams;
    invoke-virtual {v7, v4}, Landroid/widget/Button;->setBackgroundColor(I)V

    .line 343
    const-string v4, "MINIMIZE"

    invoke-virtual {v7, v4}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 344
    iget v4, v0, Lcom/android/support/Menu;->TEXT_COLOR:I

    invoke-virtual {v7, v4}, Landroid/widget/Button;->setTextColor(I)V

    .line 345
    new-instance v4, Lcom/android/support/Menu$5;

    invoke-direct {v4, v0}, Lcom/android/support/Menu$5;-><init>(Lcom/android/support/Menu;)V

    invoke-virtual {v7, v4}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 354
    iget-object v4, v0, Lcom/android/support/Menu;->mRootContainer:Landroid/widget/RelativeLayout;

    move-object/from16 v18, v9

    .end local v9    # "decode":[B
    .local v18, "decode":[B
    iget-object v9, v0, Lcom/android/support/Menu;->mCollapsed:Landroid/widget/RelativeLayout;

    invoke-virtual {v4, v9}, Landroid/widget/RelativeLayout;->addView(Landroid/view/View;)V

    .line 355
    iget-object v4, v0, Lcom/android/support/Menu;->mRootContainer:Landroid/widget/RelativeLayout;

    iget-object v9, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    invoke-virtual {v4, v9}, Landroid/widget/RelativeLayout;->addView(Landroid/view/View;)V

    .line 356
    invoke-virtual/range {p0 .. p0}, Lcom/android/support/Menu;->IconWebViewData()Ljava/lang/String;

    move-result-object v4

    if-eqz v4, :cond_2

    .line 357
    iget-object v4, v0, Lcom/android/support/Menu;->mCollapsed:Landroid/widget/RelativeLayout;

    invoke-virtual {v4, v10}, Landroid/widget/RelativeLayout;->addView(Landroid/view/View;)V

    goto :goto_2

    .line 359
    :cond_2
    iget-object v4, v0, Lcom/android/support/Menu;->mCollapsed:Landroid/widget/RelativeLayout;

    iget-object v9, v0, Lcom/android/support/Menu;->startimage:Landroid/widget/ImageView;

    invoke-virtual {v4, v9}, Landroid/widget/RelativeLayout;->addView(Landroid/view/View;)V

    .line 361
    :goto_2
    invoke-virtual {v2, v6}, Landroid/widget/RelativeLayout;->addView(Landroid/view/View;)V

    .line 362
    invoke-virtual {v2, v8}, Landroid/widget/RelativeLayout;->addView(Landroid/view/View;)V

    .line 363
    invoke-virtual {v2, v13}, Landroid/widget/RelativeLayout;->addView(Landroid/view/View;)V

    .line 364
    iget-object v4, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    invoke-virtual {v4, v2}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 365
    iget-object v4, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    invoke-virtual {v4, v15}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 366
    iget-object v4, v0, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    iget-object v9, v0, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-virtual {v4, v9}, Landroid/widget/ScrollView;->addView(Landroid/view/View;)V

    .line 367
    iget-object v4, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    iget-object v9, v0, Lcom/android/support/Menu;->scrollView:Landroid/widget/ScrollView;

    invoke-virtual {v4, v9}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 368
    invoke-virtual {v3, v5}, Landroid/widget/RelativeLayout;->addView(Landroid/view/View;)V

    .line 369
    invoke-virtual {v3, v7}, Landroid/widget/RelativeLayout;->addView(Landroid/view/View;)V

    .line 370
    iget-object v4, v0, Lcom/android/support/Menu;->mExpanded:Landroid/widget/LinearLayout;

    invoke-virtual {v4, v3}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 372
    iput-object v8, v0, Lcom/android/support/Menu;->mTitle:Landroid/widget/TextView;

    .line 373
    iput-object v15, v0, Lcom/android/support/Menu;->mSubTitle:Landroid/widget/TextView;

    .line 375
    invoke-virtual {v0, v1, v8, v15}, Lcom/android/support/Menu;->Init(Landroid/content/Context;Landroid/widget/TextView;Landroid/widget/TextView;)V

    .line 376
    return-void
.end method

.method private Button(Landroid/widget/LinearLayout;ILjava/lang/String;)V
    .locals 4
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featNum"    # I
    .param p3, "featName"    # Ljava/lang/String;

    .line 713
    new-instance v0, Landroid/widget/Button;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    .line 714
    .local v0, "button":Landroid/widget/Button;
    new-instance v1, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v2, -0x1

    invoke-direct {v1, v2, v2}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    .line 715
    .local v1, "layoutParams":Landroid/widget/LinearLayout$LayoutParams;
    const/4 v2, 0x7

    const/4 v3, 0x5

    invoke-virtual {v1, v2, v3, v2, v3}, Landroid/widget/LinearLayout$LayoutParams;->setMargins(IIII)V

    .line 716
    invoke-virtual {v0, v1}, Landroid/widget/Button;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 717
    iget v2, p0, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setTextColor(I)V

    .line 718
    const/4 v2, 0x0

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setAllCaps(Z)V

    .line 719
    sget-object v2, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setTypeface(Landroid/graphics/Typeface;)V

    .line 720
    const/high16 v2, 0x41500000    # 13.0f

    invoke-direct {p0, v0, v2}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 721
    iget v2, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    iget v3, p0, Lcom/android/support/Menu;->BORDER_COLOR:I

    invoke-direct {p0, v2, v3}, Lcom/android/support/Menu;->rect(II)Landroid/graphics/drawable/GradientDrawable;

    move-result-object v2

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 722
    invoke-static {p3}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v2

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 723
    iget v2, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setBackgroundColor(I)V

    .line 724
    new-instance v2, Lcom/android/support/Menu$10;

    invoke-direct {v2, p0, p2, p3}, Lcom/android/support/Menu$10;-><init>(Lcom/android/support/Menu;ILjava/lang/String;)V

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 760
    invoke-virtual {p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 761
    return-void
.end method

.method private ButtonLink(Landroid/widget/LinearLayout;Ljava/lang/String;Ljava/lang/String;)V
    .locals 4
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featName"    # Ljava/lang/String;
    .param p3, "url"    # Ljava/lang/String;

    .line 764
    new-instance v0, Landroid/widget/Button;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    .line 765
    .local v0, "button":Landroid/widget/Button;
    new-instance v1, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v2, -0x1

    invoke-direct {v1, v2, v2}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    .line 766
    .local v1, "layoutParams":Landroid/widget/LinearLayout$LayoutParams;
    const/4 v2, 0x7

    const/4 v3, 0x5

    invoke-virtual {v1, v2, v3, v2, v3}, Landroid/widget/LinearLayout$LayoutParams;->setMargins(IIII)V

    .line 767
    invoke-virtual {v0, v1}, Landroid/widget/Button;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 768
    const/4 v2, 0x0

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setAllCaps(Z)V

    .line 769
    sget-object v2, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setTypeface(Landroid/graphics/Typeface;)V

    .line 770
    const/high16 v2, 0x41500000    # 13.0f

    invoke-direct {p0, v0, v2}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 771
    iget v2, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    iget v3, p0, Lcom/android/support/Menu;->BORDER_COLOR:I

    invoke-direct {p0, v2, v3}, Lcom/android/support/Menu;->rect(II)Landroid/graphics/drawable/GradientDrawable;

    move-result-object v2

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 772
    iget v2, p0, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setTextColor(I)V

    .line 773
    invoke-static {p2}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v2

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 774
    iget v2, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setBackgroundColor(I)V

    .line 775
    new-instance v2, Lcom/android/support/Menu$11;

    invoke-direct {v2, p0, p3}, Lcom/android/support/Menu$11;-><init>(Lcom/android/support/Menu;Ljava/lang/String;)V

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 783
    invoke-virtual {p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 784
    return-void
.end method

.method private ButtonOnOff(Landroid/widget/LinearLayout;ILjava/lang/String;Z)V
    .locals 11
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featNum"    # I
    .param p3, "featName"    # Ljava/lang/String;
    .param p4, "switchedOn"    # Z

    .line 787
    new-instance v0, Landroid/widget/Button;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    .line 788
    .local v0, "button":Landroid/widget/Button;
    new-instance v1, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v2, -0x1

    invoke-direct {v1, v2, v2}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    .line 789
    .local v1, "layoutParams":Landroid/widget/LinearLayout$LayoutParams;
    const/4 v2, 0x7

    const/4 v3, 0x5

    invoke-virtual {v1, v2, v3, v2, v3}, Landroid/widget/LinearLayout$LayoutParams;->setMargins(IIII)V

    .line 790
    invoke-virtual {v0, v1}, Landroid/widget/Button;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 791
    iget v2, p0, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setTextColor(I)V

    .line 792
    const/4 v2, 0x0

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setAllCaps(Z)V

    .line 793
    sget-object v2, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setTypeface(Landroid/graphics/Typeface;)V

    .line 794
    const/high16 v2, 0x41500000    # 13.0f

    invoke-direct {p0, v0, v2}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 795
    iget v2, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    iget v3, p0, Lcom/android/support/Menu;->BORDER_COLOR:I

    invoke-direct {p0, v2, v3}, Lcom/android/support/Menu;->rect(II)Landroid/graphics/drawable/GradientDrawable;

    move-result-object v2

    invoke-virtual {v0, v2}, Landroid/widget/Button;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 797
    const-string v2, "OnOff_"

    const-string v3, ""

    invoke-virtual {p3, v2, v3}, Ljava/lang/String;->replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;

    move-result-object v8

    .line 798
    .local v8, "finalfeatName":Ljava/lang/String;
    invoke-static {p3, p2, p4}, Lcom/android/support/Preferences;->loadPrefBool(Ljava/lang/String;IZ)Z

    move-result v2

    .line 799
    .local v2, "isOn":Z
    if-eqz v2, :cond_0

    .line 800
    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v3, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    const-string v4, ": ON"

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    invoke-static {v3}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v3

    invoke-virtual {v0, v3}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 801
    iget v3, p0, Lcom/android/support/Menu;->BtnON:I

    invoke-virtual {v0, v3}, Landroid/widget/Button;->setBackgroundColor(I)V

    .line 802
    const/4 v2, 0x0

    move v9, v2

    goto :goto_0

    .line 804
    :cond_0
    new-instance v3, Ljava/lang/StringBuilder;

    invoke-direct {v3}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v3, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    const-string v4, ": OFF"

    invoke-virtual {v3, v4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v3

    invoke-virtual {v3}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v3

    invoke-static {v3}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v3

    invoke-virtual {v0, v3}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 805
    iget v3, p0, Lcom/android/support/Menu;->BtnOFF:I

    invoke-virtual {v0, v3}, Landroid/widget/Button;->setBackgroundColor(I)V

    .line 806
    const/4 v2, 0x1

    move v9, v2

    .line 808
    .end local v2    # "isOn":Z
    .local v9, "isOn":Z
    :goto_0
    move v4, v9

    .line 809
    .local v4, "finalIsOn":Z
    new-instance v10, Lcom/android/support/Menu$12;

    move-object v2, v10

    move-object v3, p0

    move-object v5, v8

    move v6, p2

    move-object v7, v0

    invoke-direct/range {v2 .. v7}, Lcom/android/support/Menu$12;-><init>(Lcom/android/support/Menu;ZLjava/lang/String;ILandroid/widget/Button;)V

    invoke-virtual {v0, v10}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 826
    invoke-virtual {p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 827
    return-void
.end method

.method private Category(Landroid/widget/LinearLayout;Ljava/lang/String;)V
    .locals 6
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "text"    # Ljava/lang/String;

    .line 1274
    new-instance v0, Landroid/widget/TextView;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 1275
    .local v0, "textView":Landroid/widget/TextView;
    const/high16 v1, 0x41400000    # 12.0f

    invoke-direct {p0, v0, v1}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 1276
    invoke-static {p2}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 1277
    const/16 v1, 0x11

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setGravity(I)V

    .line 1278
    iget v1, p0, Lcom/android/support/Menu;->INK:I

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextColor(I)V

    .line 1279
    sget-object v1, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    const/4 v2, 0x1

    invoke-virtual {v0, v1, v2}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    .line 1280
    invoke-virtual {v0, v2}, Landroid/widget/TextView;->setAllCaps(Z)V

    .line 1281
    invoke-direct {p0, v0}, Lcom/android/support/Menu;->track(Landroid/widget/TextView;)V

    .line 1282
    iget v1, p0, Lcom/android/support/Menu;->CHIP_BG:I

    const/4 v2, 0x2

    invoke-direct {p0, v1, v2}, Lcom/android/support/Menu;->panel(II)Landroid/graphics/drawable/GradientDrawable;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 1283
    const/16 v1, 0x8

    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v2

    const/4 v3, 0x6

    invoke-direct {p0, v3}, Lcom/android/support/Menu;->dp(I)I

    move-result v4

    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v5

    invoke-direct {p0, v3}, Lcom/android/support/Menu;->dp(I)I

    move-result v3

    invoke-virtual {v0, v2, v4, v5, v3}, Landroid/widget/TextView;->setPadding(IIII)V

    .line 1284
    new-instance v2, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v3, -0x1

    const/4 v4, -0x2

    invoke-direct {v2, v3, v4}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    .line 1286
    .local v2, "lp":Landroid/widget/LinearLayout$LayoutParams;
    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v3

    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v4

    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v1

    const/4 v5, 0x4

    invoke-direct {p0, v5}, Lcom/android/support/Menu;->dp(I)I

    move-result v5

    invoke-virtual {v2, v3, v4, v1, v5}, Landroid/widget/LinearLayout$LayoutParams;->setMargins(IIII)V

    .line 1287
    invoke-virtual {p1, v0, v2}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 1288
    return-void
.end method

.method private CheckBox(Landroid/widget/LinearLayout;ILjava/lang/String;Z)V
    .locals 2
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featNum"    # I
    .param p3, "featName"    # Ljava/lang/String;
    .param p4, "switchedOn"    # Z

    .line 1134
    new-instance v0, Landroid/widget/CheckBox;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/CheckBox;-><init>(Landroid/content/Context;)V

    .line 1135
    .local v0, "checkBox":Landroid/widget/CheckBox;
    invoke-virtual {v0, p3}, Landroid/widget/CheckBox;->setText(Ljava/lang/CharSequence;)V

    .line 1136
    iget v1, p0, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v0, v1}, Landroid/widget/CheckBox;->setTextColor(I)V

    .line 1137
    sget-object v1, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v0, v1}, Landroid/widget/CheckBox;->setTypeface(Landroid/graphics/Typeface;)V

    .line 1138
    nop

    .line 1139
    iget v1, p0, Lcom/android/support/Menu;->CheckBoxColor:I

    invoke-static {v1}, Landroid/content/res/ColorStateList;->valueOf(I)Landroid/content/res/ColorStateList;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/widget/CheckBox;->setButtonTintList(Landroid/content/res/ColorStateList;)V

    .line 1140
    invoke-static {p3, p2, p4}, Lcom/android/support/Preferences;->loadPrefBool(Ljava/lang/String;IZ)Z

    move-result v1

    invoke-virtual {v0, v1}, Landroid/widget/CheckBox;->setChecked(Z)V

    .line 1141
    new-instance v1, Lcom/android/support/Menu$17;

    invoke-direct {v1, p0, v0, p3, p2}, Lcom/android/support/Menu$17;-><init>(Lcom/android/support/Menu;Landroid/widget/CheckBox;Ljava/lang/String;I)V

    invoke-virtual {v0, v1}, Landroid/widget/CheckBox;->setOnCheckedChangeListener(Landroid/widget/CompoundButton$OnCheckedChangeListener;)V

    .line 1151
    invoke-virtual {p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1152
    return-void
.end method

.method private Collapse(Landroid/widget/LinearLayout;Ljava/lang/String;Z)V
    .locals 13
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "text"    # Ljava/lang/String;
    .param p3, "expanded"    # Z

    .line 1194
    move-object v6, p0

    move-object v7, p2

    new-instance v0, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v1, -0x1

    invoke-direct {v0, v1, v1}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    move-object v8, v0

    .line 1195
    .local v8, "layoutParamsLL":Landroid/widget/LinearLayout$LayoutParams;
    const/4 v0, 0x0

    const/4 v1, 0x5

    invoke-virtual {v8, v0, v1, v0, v0}, Landroid/widget/LinearLayout$LayoutParams;->setMargins(IIII)V

    .line 1197
    new-instance v2, Landroid/widget/LinearLayout;

    iget-object v3, v6, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v2, v3}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    move-object v9, v2

    .line 1198
    .local v9, "collapse":Landroid/widget/LinearLayout;
    invoke-virtual {v9, v8}, Landroid/widget/LinearLayout;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 1199
    const/16 v2, 0x10

    invoke-virtual {v9, v2}, Landroid/widget/LinearLayout;->setVerticalGravity(I)V

    .line 1200
    const/4 v3, 0x1

    invoke-virtual {v9, v3}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 1202
    new-instance v4, Landroid/widget/LinearLayout;

    iget-object v5, v6, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v4, v5}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    move-object v10, v4

    .line 1203
    .local v10, "collapseSub":Landroid/widget/LinearLayout;
    invoke-virtual {v10, v2}, Landroid/widget/LinearLayout;->setVerticalGravity(I)V

    .line 1204
    invoke-virtual {v10, v0, v1, v0, v1}, Landroid/widget/LinearLayout;->setPadding(IIII)V

    .line 1205
    invoke-virtual {v10, v3}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 1206
    iget v1, v6, Lcom/android/support/Menu;->CollapseSubColor:I

    invoke-virtual {v10, v1}, Landroid/widget/LinearLayout;->setBackgroundColor(I)V

    .line 1207
    const/16 v1, 0x8

    invoke-virtual {v10, v1}, Landroid/widget/LinearLayout;->setVisibility(I)V

    .line 1208
    iput-object v10, v6, Lcom/android/support/Menu;->mCollapse:Landroid/widget/LinearLayout;

    .line 1210
    new-instance v1, Landroid/widget/TextView;

    iget-object v2, v6, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v1, v2}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    move-object v11, v1

    .line 1211
    .local v11, "textView":Landroid/widget/TextView;
    iget v1, v6, Lcom/android/support/Menu;->CollapseColor:I

    invoke-virtual {v11, v1}, Landroid/widget/TextView;->setBackgroundColor(I)V

    .line 1212
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    const-string v2, "\u25bd "

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    const-string v2, " \u25bd"

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v11, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 1213
    const/16 v1, 0x11

    invoke-virtual {v11, v1}, Landroid/widget/TextView;->setGravity(I)V

    .line 1214
    iget v1, v6, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v11, v1}, Landroid/widget/TextView;->setTextColor(I)V

    .line 1215
    const/4 v1, 0x0

    invoke-virtual {v11, v1, v3}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    .line 1216
    const/16 v1, 0x14

    invoke-virtual {v11, v0, v1, v0, v1}, Landroid/widget/TextView;->setPadding(IIII)V

    .line 1218
    if-eqz p3, :cond_0

    .line 1219
    invoke-virtual {v10, v0}, Landroid/widget/LinearLayout;->setVisibility(I)V

    .line 1220
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "\u25b3 "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, " \u25b3"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-virtual {v11, v0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 1223
    :cond_0
    new-instance v12, Lcom/android/support/Menu$19;

    move-object v0, v12

    move-object v1, p0

    move/from16 v2, p3

    move-object v3, v10

    move-object v4, v11

    move-object v5, p2

    invoke-direct/range {v0 .. v5}, Lcom/android/support/Menu$19;-><init>(Lcom/android/support/Menu;ZLandroid/widget/LinearLayout;Landroid/widget/TextView;Ljava/lang/String;)V

    invoke-virtual {v11, v12}, Landroid/widget/TextView;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 1240
    invoke-virtual {v9, v11}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1241
    invoke-virtual {v9, v10}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1242
    move-object v0, p1

    invoke-virtual {p1, v9}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1243
    return-void
.end method

.method private InputLNum(Landroid/widget/LinearLayout;ILjava/lang/String;J)V
    .locals 16
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featNum"    # I
    .param p3, "featName"    # Ljava/lang/String;
    .param p4, "maxValue"    # J

    .line 968
    move-object/from16 v7, p0

    move-object/from16 v8, p3

    new-instance v0, Landroid/widget/LinearLayout;

    iget-object v1, v7, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    move-object v9, v0

    .line 969
    .local v9, "linearLayout":Landroid/widget/LinearLayout;
    new-instance v0, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v1, -0x1

    invoke-direct {v0, v1, v1}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    move-object v10, v0

    .line 970
    .local v10, "layoutParams":Landroid/widget/LinearLayout$LayoutParams;
    const/4 v0, 0x7

    const/4 v1, 0x5

    invoke-virtual {v10, v0, v1, v0, v1}, Landroid/widget/LinearLayout$LayoutParams;->setMargins(IIII)V

    .line 972
    new-instance v0, Landroid/widget/Button;

    iget-object v1, v7, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    move-object v11, v0

    .line 973
    .local v11, "button":Landroid/widget/Button;
    move/from16 v12, p2

    invoke-static {v8, v12}, Lcom/android/support/Preferences;->loadPrefLong(Ljava/lang/String;I)J

    move-result-wide v13

    .line 974
    .local v13, "num":J
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v0, v8}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, ": <font color=\'"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    iget-object v1, v7, Lcom/android/support/Menu;->NumberTxtColor:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, "\'>"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, v13, v14}, Ljava/lang/StringBuilder;->append(J)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, "</font>"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-static {v0}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v0

    invoke-virtual {v11, v0}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 975
    const/4 v0, 0x0

    invoke-virtual {v11, v0}, Landroid/widget/Button;->setAllCaps(Z)V

    .line 976
    sget-object v0, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v11, v0}, Landroid/widget/Button;->setTypeface(Landroid/graphics/Typeface;)V

    .line 977
    const/high16 v0, 0x41500000    # 13.0f

    invoke-direct {v7, v11, v0}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 978
    iget v0, v7, Lcom/android/support/Menu;->BTN_COLOR:I

    iget v1, v7, Lcom/android/support/Menu;->BORDER_COLOR:I

    invoke-direct {v7, v0, v1}, Lcom/android/support/Menu;->rect(II)Landroid/graphics/drawable/GradientDrawable;

    move-result-object v0

    invoke-virtual {v11, v0}, Landroid/widget/Button;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 979
    invoke-virtual {v11, v10}, Landroid/widget/Button;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 980
    iget v0, v7, Lcom/android/support/Menu;->BTN_COLOR:I

    invoke-virtual {v11, v0}, Landroid/widget/Button;->setBackgroundColor(I)V

    .line 981
    iget v0, v7, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v11, v0}, Landroid/widget/Button;->setTextColor(I)V

    .line 982
    new-instance v15, Lcom/android/support/Menu$15;

    move-object v0, v15

    move-object/from16 v1, p0

    move-wide/from16 v2, p4

    move-object v4, v11

    move-object/from16 v5, p3

    move/from16 v6, p2

    invoke-direct/range {v0 .. v6}, Lcom/android/support/Menu$15;-><init>(Lcom/android/support/Menu;JLandroid/widget/Button;Ljava/lang/String;I)V

    invoke-virtual {v11, v15}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 1054
    invoke-virtual {v9, v11}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1055
    move-object/from16 v0, p1

    invoke-virtual {v0, v9}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1056
    return-void
.end method

.method private InputNum(Landroid/widget/LinearLayout;ILjava/lang/String;I)V
    .locals 11
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featNum"    # I
    .param p3, "featName"    # Ljava/lang/String;
    .param p4, "maxValue"    # I

    .line 878
    new-instance v0, Landroid/widget/LinearLayout;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    .line 879
    .local v0, "linearLayout":Landroid/widget/LinearLayout;
    new-instance v1, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v2, -0x1

    invoke-direct {v1, v2, v2}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    .line 880
    .local v1, "layoutParams":Landroid/widget/LinearLayout$LayoutParams;
    const/4 v2, 0x7

    const/4 v3, 0x5

    invoke-virtual {v1, v2, v3, v2, v3}, Landroid/widget/LinearLayout$LayoutParams;->setMargins(IIII)V

    .line 882
    new-instance v2, Landroid/widget/Button;

    iget-object v3, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v2, v3}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    .line 883
    .local v2, "button":Landroid/widget/Button;
    invoke-static {p3, p2}, Lcom/android/support/Preferences;->loadPrefInt(Ljava/lang/String;I)I

    move-result v3

    .line 884
    .local v3, "num":I
    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v4, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    const-string v5, ": <font color=\'"

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    iget-object v5, p0, Lcom/android/support/Menu;->NumberTxtColor:Ljava/lang/String;

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    const-string v5, "\'>"

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4, v3}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v4

    const-string v5, "</font>"

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-static {v4}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v4

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 885
    const/4 v4, 0x0

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setAllCaps(Z)V

    .line 886
    sget-object v4, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setTypeface(Landroid/graphics/Typeface;)V

    .line 887
    const/high16 v4, 0x41500000    # 13.0f

    invoke-direct {p0, v2, v4}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 888
    iget v4, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    iget v5, p0, Lcom/android/support/Menu;->BORDER_COLOR:I

    invoke-direct {p0, v4, v5}, Lcom/android/support/Menu;->rect(II)Landroid/graphics/drawable/GradientDrawable;

    move-result-object v4

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 889
    invoke-virtual {v2, v1}, Landroid/widget/Button;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 890
    iget v4, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setBackgroundColor(I)V

    .line 891
    iget v4, p0, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setTextColor(I)V

    .line 892
    new-instance v10, Lcom/android/support/Menu$14;

    move-object v4, v10

    move-object v5, p0

    move v6, p4

    move-object v7, v2

    move-object v8, p3

    move v9, p2

    invoke-direct/range {v4 .. v9}, Lcom/android/support/Menu$14;-><init>(Lcom/android/support/Menu;ILandroid/widget/Button;Ljava/lang/String;I)V

    invoke-virtual {v2, v10}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 963
    invoke-virtual {v0, v2}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 964
    invoke-virtual {p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 965
    return-void
.end method

.method private InputText(Landroid/widget/LinearLayout;ILjava/lang/String;)V
    .locals 6
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featNum"    # I
    .param p3, "featName"    # Ljava/lang/String;

    .line 1059
    new-instance v0, Landroid/widget/LinearLayout;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    .line 1060
    .local v0, "linearLayout":Landroid/widget/LinearLayout;
    new-instance v1, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v2, -0x1

    invoke-direct {v1, v2, v2}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    .line 1061
    .local v1, "layoutParams":Landroid/widget/LinearLayout$LayoutParams;
    const/4 v2, 0x7

    const/4 v3, 0x5

    invoke-virtual {v1, v2, v3, v2, v3}, Landroid/widget/LinearLayout$LayoutParams;->setMargins(IIII)V

    .line 1063
    new-instance v2, Landroid/widget/Button;

    iget-object v3, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v2, v3}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    .line 1065
    .local v2, "button":Landroid/widget/Button;
    invoke-static {p3, p2}, Lcom/android/support/Preferences;->loadPrefString(Ljava/lang/String;I)Ljava/lang/String;

    move-result-object v3

    .line 1066
    .local v3, "string":Ljava/lang/String;
    new-instance v4, Ljava/lang/StringBuilder;

    invoke-direct {v4}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v4, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    const-string v5, ": <font color=\'"

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    iget-object v5, p0, Lcom/android/support/Menu;->NumberTxtColor:Ljava/lang/String;

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    const-string v5, "\'>"

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    const-string v5, "</font>"

    invoke-virtual {v4, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v4

    invoke-virtual {v4}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v4

    invoke-static {v4}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v4

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 1068
    const/4 v4, 0x0

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setAllCaps(Z)V

    .line 1069
    sget-object v4, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setTypeface(Landroid/graphics/Typeface;)V

    .line 1070
    const/high16 v4, 0x41500000    # 13.0f

    invoke-direct {p0, v2, v4}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 1071
    iget v4, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    iget v5, p0, Lcom/android/support/Menu;->BORDER_COLOR:I

    invoke-direct {p0, v4, v5}, Lcom/android/support/Menu;->rect(II)Landroid/graphics/drawable/GradientDrawable;

    move-result-object v4

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 1072
    invoke-virtual {v2, v1}, Landroid/widget/Button;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 1073
    iget v4, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setBackgroundColor(I)V

    .line 1074
    iget v4, p0, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setTextColor(I)V

    .line 1075
    new-instance v4, Lcom/android/support/Menu$16;

    invoke-direct {v4, p0, v2, p3, p2}, Lcom/android/support/Menu$16;-><init>(Lcom/android/support/Menu;Landroid/widget/Button;Ljava/lang/String;I)V

    invoke-virtual {v2, v4}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 1129
    invoke-virtual {v0, v2}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1130
    invoke-virtual {p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1131
    return-void
.end method

.method private RadioButton(Landroid/widget/LinearLayout;ILjava/lang/String;Ljava/lang/String;)V
    .locals 19
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featNum"    # I
    .param p3, "featName"    # Ljava/lang/String;
    .param p4, "list"    # Ljava/lang/String;

    .line 1156
    move-object/from16 v8, p0

    move-object/from16 v9, p3

    new-instance v0, Ljava/util/LinkedList;

    const-string v1, ","

    move-object/from16 v10, p4

    invoke-virtual {v10, v1}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;

    move-result-object v1

    invoke-static {v1}, Ljava/util/Arrays;->asList([Ljava/lang/Object;)Ljava/util/List;

    move-result-object v1

    invoke-direct {v0, v1}, Ljava/util/LinkedList;-><init>(Ljava/util/Collection;)V

    move-object v11, v0

    .line 1158
    .local v11, "lists":Ljava/util/List;, "Ljava/util/List<Ljava/lang/String;>;"
    new-instance v0, Landroid/widget/TextView;

    iget-object v1, v8, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    move-object v12, v0

    .line 1159
    .local v12, "textView":Landroid/widget/TextView;
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v0, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, ":"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-virtual {v12, v0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 1160
    iget v0, v8, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v12, v0}, Landroid/widget/TextView;->setTextColor(I)V

    .line 1162
    new-instance v0, Landroid/widget/RadioGroup;

    iget-object v1, v8, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/RadioGroup;-><init>(Landroid/content/Context;)V

    move-object v13, v0

    .line 1163
    .local v13, "radioGroup":Landroid/widget/RadioGroup;
    const/16 v0, 0xa

    const/4 v1, 0x5

    invoke-virtual {v13, v0, v1, v0, v1}, Landroid/widget/RadioGroup;->setPadding(IIII)V

    .line 1164
    const/4 v14, 0x1

    invoke-virtual {v13, v14}, Landroid/widget/RadioGroup;->setOrientation(I)V

    .line 1165
    invoke-virtual {v13, v12}, Landroid/widget/RadioGroup;->addView(Landroid/view/View;)V

    .line 1167
    const/4 v0, 0x0

    move v15, v0

    .local v15, "i":I
    :goto_0
    invoke-interface {v11}, Ljava/util/List;->size()I

    move-result v0

    if-ge v15, v0, :cond_0

    .line 1168
    new-instance v0, Landroid/widget/RadioButton;

    iget-object v1, v8, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/RadioButton;-><init>(Landroid/content/Context;)V

    move-object v7, v0

    .line 1169
    .local v7, "Radioo":Landroid/widget/RadioButton;
    move-object/from16 v3, p3

    .local v3, "finalfeatName":Ljava/lang/String;
    invoke-interface {v11, v15}, Ljava/util/List;->get(I)Ljava/lang/Object;

    move-result-object v0

    move-object/from16 v16, v0

    check-cast v16, Ljava/lang/String;

    .line 1170
    .local v16, "radioName":Ljava/lang/String;
    new-instance v17, Lcom/android/support/Menu$18;

    move-object/from16 v0, v17

    move-object/from16 v1, p0

    move-object v2, v12

    move-object/from16 v4, v16

    move/from16 v5, p2

    move-object v6, v13

    move-object/from16 v18, v7

    .end local v7    # "Radioo":Landroid/widget/RadioButton;
    .local v18, "Radioo":Landroid/widget/RadioButton;
    invoke-direct/range {v0 .. v7}, Lcom/android/support/Menu$18;-><init>(Lcom/android/support/Menu;Landroid/widget/TextView;Ljava/lang/String;Ljava/lang/String;ILandroid/widget/RadioGroup;Landroid/widget/RadioButton;)V

    .line 1176
    .local v0, "first_radio_listener":Landroid/view/View$OnClickListener;
    sget-object v1, Ljava/lang/System;->out:Ljava/io/PrintStream;

    invoke-interface {v11, v15}, Ljava/util/List;->get(I)Ljava/lang/Object;

    move-result-object v2

    check-cast v2, Ljava/lang/String;

    invoke-virtual {v1, v2}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V

    .line 1177
    invoke-interface {v11, v15}, Ljava/util/List;->get(I)Ljava/lang/Object;

    move-result-object v1

    check-cast v1, Ljava/lang/CharSequence;

    move-object/from16 v2, v18

    .end local v18    # "Radioo":Landroid/widget/RadioButton;
    .local v2, "Radioo":Landroid/widget/RadioButton;
    invoke-virtual {v2, v1}, Landroid/widget/RadioButton;->setText(Ljava/lang/CharSequence;)V

    .line 1178
    const v1, -0x333334

    invoke-virtual {v2, v1}, Landroid/widget/RadioButton;->setTextColor(I)V

    .line 1179
    nop

    .line 1180
    iget v1, v8, Lcom/android/support/Menu;->RadioColor:I

    invoke-static {v1}, Landroid/content/res/ColorStateList;->valueOf(I)Landroid/content/res/ColorStateList;

    move-result-object v1

    invoke-virtual {v2, v1}, Landroid/widget/RadioButton;->setButtonTintList(Landroid/content/res/ColorStateList;)V

    .line 1181
    invoke-virtual {v2, v0}, Landroid/widget/RadioButton;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 1182
    invoke-virtual {v13, v2}, Landroid/widget/RadioGroup;->addView(Landroid/view/View;)V

    .line 1167
    .end local v0    # "first_radio_listener":Landroid/view/View$OnClickListener;
    .end local v2    # "Radioo":Landroid/widget/RadioButton;
    .end local v3    # "finalfeatName":Ljava/lang/String;
    .end local v16    # "radioName":Ljava/lang/String;
    add-int/lit8 v15, v15, 0x1

    goto :goto_0

    .line 1185
    .end local v15    # "i":I
    :cond_0
    move/from16 v0, p2

    invoke-static {v9, v0}, Lcom/android/support/Preferences;->loadPrefInt(Ljava/lang/String;I)I

    move-result v1

    .line 1186
    .local v1, "index":I
    if-lez v1, :cond_1

    .line 1187
    new-instance v2, Ljava/lang/StringBuilder;

    invoke-direct {v2}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v2, v9}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string v3, ": <font color=\'"

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    iget-object v3, v8, Lcom/android/support/Menu;->NumberTxtColor:Ljava/lang/String;

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    const-string v3, "\'>"

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    add-int/lit8 v3, v1, -0x1

    invoke-interface {v11, v3}, Ljava/util/List;->get(I)Ljava/lang/Object;

    move-result-object v3

    check-cast v3, Ljava/lang/String;

    invoke-virtual {v2, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v2

    invoke-virtual {v2}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v2

    invoke-static {v2}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v2

    invoke-virtual {v12, v2}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 1188
    invoke-virtual {v13, v1}, Landroid/widget/RadioGroup;->getChildAt(I)Landroid/view/View;

    move-result-object v2

    check-cast v2, Landroid/widget/RadioButton;

    invoke-virtual {v2, v14}, Landroid/widget/RadioButton;->setChecked(Z)V

    .line 1190
    :cond_1
    move-object/from16 v2, p1

    invoke-virtual {v2, v13}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1191
    return-void
.end method

.method private SeekBar(Landroid/widget/LinearLayout;ILjava/lang/String;II)V
    .locals 16
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featNum"    # I
    .param p3, "featName"    # Ljava/lang/String;
    .param p4, "min"    # I
    .param p5, "max"    # I

    .line 656
    move-object/from16 v6, p0

    move-object/from16 v7, p3

    move/from16 v8, p2

    invoke-static {v7, v8}, Lcom/android/support/Preferences;->loadPrefInt(Ljava/lang/String;I)I

    move-result v9

    .line 657
    .local v9, "loadedProg":I
    new-instance v0, Landroid/widget/LinearLayout;

    iget-object v1, v6, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    move-object v10, v0

    .line 658
    .local v10, "linearLayout":Landroid/widget/LinearLayout;
    const/4 v0, 0x5

    const/4 v1, 0x0

    const/16 v2, 0xa

    invoke-virtual {v10, v2, v0, v1, v0}, Landroid/widget/LinearLayout;->setPadding(IIII)V

    .line 659
    const/4 v0, 0x1

    invoke-virtual {v10, v0}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 660
    const/16 v0, 0x11

    invoke-virtual {v10, v0}, Landroid/widget/LinearLayout;->setGravity(I)V

    .line 662
    new-instance v0, Landroid/widget/TextView;

    iget-object v1, v6, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    move-object v11, v0

    .line 663
    .local v11, "textView":Landroid/widget/TextView;
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v0, v7}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, ": <font color=\'"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    iget-object v1, v6, Lcom/android/support/Menu;->NumberTxtColor:Ljava/lang/String;

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, "\'>"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    if-nez v9, :cond_0

    move/from16 v1, p5

    goto :goto_0

    :cond_0
    move v1, v9

    :goto_0
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    invoke-static {v0}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v0

    invoke-virtual {v11, v0}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 664
    iget v0, v6, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v11, v0}, Landroid/widget/TextView;->setTextColor(I)V

    .line 665
    sget-object v0, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v11, v0}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;)V

    .line 666
    const/high16 v0, 0x41500000    # 13.0f

    invoke-direct {v6, v11, v0}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 668
    new-instance v0, Landroid/widget/SeekBar;

    iget-object v1, v6, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/SeekBar;-><init>(Landroid/content/Context;)V

    move-object v12, v0

    .line 669
    .local v12, "seekBar":Landroid/widget/SeekBar;
    const/16 v0, 0x19

    const/16 v1, 0x23

    invoke-virtual {v12, v0, v2, v1, v2}, Landroid/widget/SeekBar;->setPadding(IIII)V

    .line 670
    move/from16 v13, p5

    invoke-virtual {v12, v13}, Landroid/widget/SeekBar;->setMax(I)V

    .line 671
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v1, 0x1a

    if-lt v0, v1, :cond_1

    .line 672
    move/from16 v14, p4

    invoke-virtual {v12, v14}, Landroid/widget/SeekBar;->setMin(I)V

    goto :goto_1

    .line 671
    :cond_1
    move/from16 v14, p4

    .line 673
    :goto_1
    if-nez v9, :cond_2

    move v0, v13

    goto :goto_2

    :cond_2
    move v0, v9

    :goto_2
    invoke-virtual {v12, v0}, Landroid/widget/SeekBar;->setProgress(I)V

    .line 674
    invoke-virtual {v12}, Landroid/widget/SeekBar;->getThumb()Landroid/graphics/drawable/Drawable;

    move-result-object v0

    iget v1, v6, Lcom/android/support/Menu;->SeekBarColor:I

    sget-object v2, Landroid/graphics/PorterDuff$Mode;->SRC_ATOP:Landroid/graphics/PorterDuff$Mode;

    invoke-virtual {v0, v1, v2}, Landroid/graphics/drawable/Drawable;->setColorFilter(ILandroid/graphics/PorterDuff$Mode;)V

    .line 675
    invoke-virtual {v12}, Landroid/widget/SeekBar;->getProgressDrawable()Landroid/graphics/drawable/Drawable;

    move-result-object v0

    iget v1, v6, Lcom/android/support/Menu;->SeekBarProgressColor:I

    sget-object v2, Landroid/graphics/PorterDuff$Mode;->SRC_ATOP:Landroid/graphics/PorterDuff$Mode;

    invoke-virtual {v0, v1, v2}, Landroid/graphics/drawable/Drawable;->setColorFilter(ILandroid/graphics/PorterDuff$Mode;)V

    .line 676
    new-instance v15, Lcom/android/support/Menu$9;

    move-object v0, v15

    move-object/from16 v1, p0

    move/from16 v2, p4

    move-object/from16 v3, p3

    move/from16 v4, p2

    move-object v5, v11

    invoke-direct/range {v0 .. v5}, Lcom/android/support/Menu$9;-><init>(Lcom/android/support/Menu;ILjava/lang/String;ILandroid/widget/TextView;)V

    invoke-virtual {v12, v15}, Landroid/widget/SeekBar;->setOnSeekBarChangeListener(Landroid/widget/SeekBar$OnSeekBarChangeListener;)V

    .line 692
    invoke-virtual {v10, v11}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 693
    invoke-virtual {v10, v12}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 695
    move-object/from16 v0, p1

    invoke-virtual {v0, v10}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 696
    return-void
.end method

.method private Spinner(Landroid/widget/LinearLayout;ILjava/lang/String;Ljava/lang/String;)V
    .locals 8
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featNum"    # I
    .param p3, "featName"    # Ljava/lang/String;
    .param p4, "list"    # Ljava/lang/String;

    .line 830
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    const-string v1, "spinner "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p2}, Ljava/lang/StringBuilder;->append(I)Ljava/lang/StringBuilder;

    move-result-object v0

    const-string v1, " "

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0, p4}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v0

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const-string v1, "Mod_Menu"

    invoke-static {v1, v0}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 831
    new-instance v0, Ljava/util/LinkedList;

    const-string v1, ","

    invoke-virtual {p4, v1}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;

    move-result-object v1

    invoke-static {v1}, Ljava/util/Arrays;->asList([Ljava/lang/Object;)Ljava/util/List;

    move-result-object v1

    invoke-direct {v0, v1}, Ljava/util/LinkedList;-><init>(Ljava/util/Collection;)V

    .line 835
    .local v0, "lists":Ljava/util/List;, "Ljava/util/List<Ljava/lang/String;>;"
    new-instance v1, Landroid/widget/LinearLayout;

    iget-object v2, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v1, v2}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    .line 836
    .local v1, "linearLayout2":Landroid/widget/LinearLayout;
    new-instance v2, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v3, -0x1

    const/4 v4, -0x2

    invoke-direct {v2, v3, v4}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    .line 837
    .local v2, "layoutParams2":Landroid/widget/LinearLayout$LayoutParams;
    const/4 v3, 0x7

    const/4 v4, 0x2

    invoke-virtual {v2, v3, v4, v3, v4}, Landroid/widget/LinearLayout$LayoutParams;->setMargins(IIII)V

    .line 838
    const/4 v3, 0x1

    invoke-virtual {v1, v3}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 839
    iget v4, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    iget v5, p0, Lcom/android/support/Menu;->BORDER_COLOR:I

    invoke-direct {p0, v4, v5}, Lcom/android/support/Menu;->rect(II)Landroid/graphics/drawable/GradientDrawable;

    move-result-object v4

    invoke-virtual {v1, v4}, Landroid/widget/LinearLayout;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 840
    invoke-virtual {v1, v2}, Landroid/widget/LinearLayout;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 842
    new-instance v4, Landroid/widget/Spinner;

    iget-object v5, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v4, v5, v3}, Landroid/widget/Spinner;-><init>(Landroid/content/Context;I)V

    .line 843
    .local v4, "spinner":Landroid/widget/Spinner;
    invoke-virtual {v4, v2}, Landroid/widget/Spinner;->setLayoutParams(Landroid/view/ViewGroup$LayoutParams;)V

    .line 844
    invoke-virtual {v4}, Landroid/widget/Spinner;->getBackground()Landroid/graphics/drawable/Drawable;

    move-result-object v5

    iget v6, p0, Lcom/android/support/Menu;->BORDER_COLOR:I

    sget-object v7, Landroid/graphics/PorterDuff$Mode;->SRC_ATOP:Landroid/graphics/PorterDuff$Mode;

    invoke-virtual {v5, v6, v7}, Landroid/graphics/drawable/Drawable;->setColorFilter(ILandroid/graphics/PorterDuff$Mode;)V

    .line 846
    new-instance v5, Landroid/widget/ArrayAdapter;

    iget-object v6, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    const v7, 0x1090009

    invoke-direct {v5, v6, v7, v0}, Landroid/widget/ArrayAdapter;-><init>(Landroid/content/Context;ILjava/util/List;)V

    .line 847
    .local v5, "aa":Landroid/widget/ArrayAdapter;
    invoke-virtual {v5, v7}, Landroid/widget/ArrayAdapter;->setDropDownViewResource(I)V

    .line 849
    invoke-virtual {v4, v5}, Landroid/widget/Spinner;->setAdapter(Landroid/widget/SpinnerAdapter;)V

    .line 852
    invoke-interface {v0}, Ljava/util/List;->isEmpty()Z

    move-result v6

    if-nez v6, :cond_2

    .line 853
    invoke-static {p3, p2}, Lcom/android/support/Preferences;->loadPrefInt(Ljava/lang/String;I)I

    move-result v6

    .line 854
    .local v6, "savedSel":I
    if-gez v6, :cond_0

    const/4 v6, 0x0

    .line 855
    :cond_0
    invoke-interface {v0}, Ljava/util/List;->size()I

    move-result v7

    if-lt v6, v7, :cond_1

    invoke-interface {v0}, Ljava/util/List;->size()I

    move-result v7

    add-int/lit8 v6, v7, -0x1

    .line 856
    :cond_1
    invoke-virtual {v4, v6}, Landroid/widget/Spinner;->setSelection(I)V

    .line 858
    .end local v6    # "savedSel":I
    :cond_2
    new-instance v3, Lcom/android/support/Menu$13;

    invoke-direct {v3, p0, v4, p2}, Lcom/android/support/Menu$13;-><init>(Lcom/android/support/Menu;Landroid/widget/Spinner;I)V

    invoke-virtual {v4, v3}, Landroid/widget/Spinner;->setOnItemSelectedListener(Landroid/widget/AdapterView$OnItemSelectedListener;)V

    .line 873
    invoke-virtual {v1, v4}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 874
    invoke-virtual {p1, v1}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 875
    return-void
.end method

.method private Switch(Landroid/widget/LinearLayout;ILjava/lang/String;Z)V
    .locals 7
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "featNum"    # I
    .param p3, "featName"    # Ljava/lang/String;
    .param p4, "swiOn"    # Z

    .line 607
    new-instance v0, Landroid/widget/Switch;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/Switch;-><init>(Landroid/content/Context;)V

    .line 608
    .local v0, "switchR":Landroid/widget/Switch;
    new-instance v1, Landroid/content/res/ColorStateList;

    const/4 v2, 0x0

    new-array v3, v2, [I

    const/4 v4, 0x3

    new-array v4, v4, [[I

    const v5, -0x101009e

    filled-new-array {v5}, [I

    move-result-object v5

    aput-object v5, v4, v2

    const v5, 0x10100a0

    filled-new-array {v5}, [I

    move-result-object v5

    const/4 v6, 0x1

    aput-object v5, v4, v6

    const/4 v5, 0x2

    aput-object v3, v4, v5

    iget v3, p0, Lcom/android/support/Menu;->ToggleON:I

    iget v5, p0, Lcom/android/support/Menu;->ToggleOFF:I

    const v6, -0xffff01

    filled-new-array {v6, v3, v5}, [I

    move-result-object v3

    invoke-direct {v1, v4, v3}, Landroid/content/res/ColorStateList;-><init>([[I[I)V

    .line 621
    .local v1, "buttonStates":Landroid/content/res/ColorStateList;
    nop

    .line 623
    :try_start_0
    invoke-virtual {v0}, Landroid/widget/Switch;->getThumbDrawable()Landroid/graphics/drawable/Drawable;

    move-result-object v3

    invoke-virtual {v3, v1}, Landroid/graphics/drawable/Drawable;->setTintList(Landroid/content/res/ColorStateList;)V

    .line 624
    invoke-virtual {v0}, Landroid/widget/Switch;->getTrackDrawable()Landroid/graphics/drawable/Drawable;

    move-result-object v3

    invoke-virtual {v3, v1}, Landroid/graphics/drawable/Drawable;->setTintList(Landroid/content/res/ColorStateList;)V
    :try_end_0
    .catch Ljava/lang/NullPointerException; {:try_start_0 .. :try_end_0} :catch_0

    .line 627
    goto :goto_0

    .line 625
    :catch_0
    move-exception v3

    .line 626
    .local v3, "ex":Ljava/lang/NullPointerException;
    const-string v4, "Mod_Menu"

    invoke-static {v3}, Ljava/lang/String;->valueOf(Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v5

    invoke-static {v4, v5}, Landroid/util/Log;->d(Ljava/lang/String;Ljava/lang/String;)I

    .line 629
    .end local v3    # "ex":Ljava/lang/NullPointerException;
    :goto_0
    invoke-virtual {v0, p3}, Landroid/widget/Switch;->setText(Ljava/lang/CharSequence;)V

    .line 630
    const/high16 v3, 0x41500000    # 13.0f

    invoke-direct {p0, v0, v3}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 631
    iget v3, p0, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v0, v3}, Landroid/widget/Switch;->setTextColor(I)V

    .line 632
    sget-object v3, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v0, v3}, Landroid/widget/Switch;->setTypeface(Landroid/graphics/Typeface;)V

    .line 633
    const/16 v3, 0xa

    const/4 v4, 0x5

    invoke-virtual {v0, v3, v4, v2, v4}, Landroid/widget/Switch;->setPadding(IIII)V

    .line 634
    invoke-static {p3, p2, p4}, Lcom/android/support/Preferences;->loadPrefBool(Ljava/lang/String;IZ)Z

    move-result v2

    invoke-virtual {v0, v2}, Landroid/widget/Switch;->setChecked(Z)V

    .line 635
    new-instance v2, Lcom/android/support/Menu$8;

    invoke-direct {v2, p0, p3, p2, v0}, Lcom/android/support/Menu$8;-><init>(Lcom/android/support/Menu;Ljava/lang/String;ILandroid/widget/Switch;)V

    invoke-virtual {v0, v2}, Landroid/widget/Switch;->setOnCheckedChangeListener(Landroid/widget/CompoundButton$OnCheckedChangeListener;)V

    .line 652
    invoke-virtual {p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 653
    return-void
.end method

.method private TextView(Landroid/widget/LinearLayout;Ljava/lang/String;)V
    .locals 5
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "text"    # Ljava/lang/String;

    .line 1292
    const-string v0, "\u81ea\u68c0"

    invoke-virtual {p2, v0}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v0

    if-eqz v0, :cond_0

    .line 1293
    invoke-direct {p0, p1, p2}, Lcom/android/support/Menu;->statusRow(Landroid/widget/LinearLayout;Ljava/lang/String;)V

    .line 1294
    return-void

    .line 1296
    :cond_0
    new-instance v0, Landroid/widget/TextView;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 1297
    .local v0, "textView":Landroid/widget/TextView;
    const/high16 v1, 0x41500000    # 13.0f

    invoke-direct {p0, v0, v1}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 1298
    invoke-static {p2}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;

    move-result-object v1

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 1299
    iget v1, p0, Lcom/android/support/Menu;->TEXT_COLOR_2:I

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTextColor(I)V

    .line 1300
    sget-object v1, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v0, v1}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;)V

    .line 1301
    const/16 v1, 0xc

    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v2

    const/4 v3, 0x5

    invoke-direct {p0, v3}, Lcom/android/support/Menu;->dp(I)I

    move-result v4

    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v1

    invoke-direct {p0, v3}, Lcom/android/support/Menu;->dp(I)I

    move-result v3

    invoke-virtual {v0, v2, v4, v1, v3}, Landroid/widget/TextView;->setPadding(IIII)V

    .line 1302
    invoke-virtual {p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1303
    return-void
.end method

.method private WebTextView(Landroid/widget/LinearLayout;Ljava/lang/String;)V
    .locals 3
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "text"    # Ljava/lang/String;

    .line 1356
    new-instance v0, Landroid/webkit/WebView;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/webkit/WebView;-><init>(Landroid/content/Context;)V

    .line 1357
    .local v0, "wView":Landroid/webkit/WebView;
    const-string v1, "text/html"

    const-string v2, "utf-8"

    invoke-virtual {v0, p2, v1, v2}, Landroid/webkit/WebView;->loadData(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;)V

    .line 1358
    const/4 v1, 0x0

    invoke-virtual {v0, v1}, Landroid/webkit/WebView;->setBackgroundColor(I)V

    .line 1359
    const/4 v2, 0x5

    invoke-virtual {v0, v1, v2, v1, v2}, Landroid/webkit/WebView;->setPadding(IIII)V

    .line 1360
    invoke-virtual {v0}, Landroid/webkit/WebView;->getSettings()Landroid/webkit/WebSettings;

    move-result-object v1

    const/4 v2, 0x2

    invoke-virtual {v1, v2}, Landroid/webkit/WebSettings;->setCacheMode(I)V

    .line 1361
    invoke-virtual {p1, v0}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1362
    return-void
.end method

.method static synthetic access$000(Lcom/android/support/Menu;Landroid/widget/LinearLayout;Ljava/lang/String;)V
    .locals 0
    .param p0, "x0"    # Lcom/android/support/Menu;
    .param p1, "x1"    # Landroid/widget/LinearLayout;
    .param p2, "x2"    # Ljava/lang/String;

    .line 69
    invoke-direct {p0, p1, p2}, Lcom/android/support/Menu;->Category(Landroid/widget/LinearLayout;Ljava/lang/String;)V

    return-void
.end method

.method static synthetic access$100(Lcom/android/support/Menu;Landroid/widget/LinearLayout;ILjava/lang/String;)V
    .locals 0
    .param p0, "x0"    # Lcom/android/support/Menu;
    .param p1, "x1"    # Landroid/widget/LinearLayout;
    .param p2, "x2"    # I
    .param p3, "x3"    # Ljava/lang/String;

    .line 69
    invoke-direct {p0, p1, p2, p3}, Lcom/android/support/Menu;->Button(Landroid/widget/LinearLayout;ILjava/lang/String;)V

    return-void
.end method

.method static synthetic access$200(Lcom/android/support/Menu;[Ljava/lang/String;Landroid/widget/LinearLayout;)V
    .locals 0
    .param p0, "x0"    # Lcom/android/support/Menu;
    .param p1, "x1"    # [Ljava/lang/String;
    .param p2, "x2"    # Landroid/widget/LinearLayout;

    .line 69
    invoke-direct {p0, p1, p2}, Lcom/android/support/Menu;->featureList([Ljava/lang/String;Landroid/widget/LinearLayout;)V

    return-void
.end method

.method static synthetic access$300(Lcom/android/support/Menu;)Z
    .locals 1
    .param p0, "x0"    # Lcom/android/support/Menu;

    .line 69
    invoke-direct {p0}, Lcom/android/support/Menu;->isViewCollapsed()Z

    move-result v0

    return v0
.end method

.method static synthetic access$400(Lcom/android/support/Menu;I)V
    .locals 0
    .param p0, "x0"    # Lcom/android/support/Menu;
    .param p1, "x1"    # I

    .line 69
    invoke-direct {p0, p1}, Lcom/android/support/Menu;->applyUiScale(I)V

    return-void
.end method

.method static synthetic access$500(Lcom/android/support/Menu;Landroid/widget/TextView;F)V
    .locals 0
    .param p0, "x0"    # Lcom/android/support/Menu;
    .param p1, "x1"    # Landroid/widget/TextView;
    .param p2, "x2"    # F

    .line 69
    invoke-direct {p0, p1, p2}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    return-void
.end method

.method private addHotSwitchHeader(Landroid/widget/LinearLayout;Z)Landroid/widget/LinearLayout;
    .locals 6
    .param p1, "parent"    # Landroid/widget/LinearLayout;
    .param p2, "open"    # Z

    .line 1247
    new-instance v0, Landroid/widget/LinearLayout;

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v0, v1}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    .line 1248
    .local v0, "box":Landroid/widget/LinearLayout;
    const/4 v1, 0x1

    invoke-virtual {v0, v1}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 1249
    const/4 v2, 0x0

    const/16 v3, 0x8

    if-eqz p2, :cond_0

    const/4 v4, 0x0

    goto :goto_0

    :cond_0
    const/16 v4, 0x8

    :goto_0
    invoke-virtual {v0, v4}, Landroid/widget/LinearLayout;->setVisibility(I)V

    .line 1251
    new-instance v4, Landroid/widget/Button;

    iget-object v5, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v4, v5}, Landroid/widget/Button;-><init>(Landroid/content/Context;)V

    .line 1252
    .local v4, "header":Landroid/widget/Button;
    invoke-virtual {v4, v2}, Landroid/widget/Button;->setAllCaps(Z)V

    .line 1253
    sget-object v2, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v4, v2, v1}, Landroid/widget/Button;->setTypeface(Landroid/graphics/Typeface;I)V

    .line 1254
    iget v1, p0, Lcom/android/support/Menu;->TEXT_COLOR:I

    invoke-virtual {v4, v1}, Landroid/widget/Button;->setTextColor(I)V

    .line 1255
    iget v1, p0, Lcom/android/support/Menu;->BTN_COLOR:I

    iget v2, p0, Lcom/android/support/Menu;->BORDER_COLOR:I

    invoke-direct {p0, v1, v2}, Lcom/android/support/Menu;->rect(II)Landroid/graphics/drawable/GradientDrawable;

    move-result-object v1

    invoke-virtual {v4, v1}, Landroid/widget/Button;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 1256
    const/16 v1, 0x10

    invoke-virtual {v4, v1}, Landroid/widget/Button;->setGravity(I)V

    .line 1257
    const/16 v1, 0xa

    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v2

    invoke-direct {p0, v3}, Lcom/android/support/Menu;->dp(I)I

    move-result v5

    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v1

    invoke-direct {p0, v3}, Lcom/android/support/Menu;->dp(I)I

    move-result v3

    invoke-virtual {v4, v2, v5, v1, v3}, Landroid/widget/Button;->setPadding(IIII)V

    .line 1258
    new-instance v1, Ljava/lang/StringBuilder;

    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V

    if-eqz p2, :cond_1

    const-string v2, "\u25be "

    goto :goto_1

    :cond_1
    const-string v2, "\u25b8 "

    :goto_1
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    const-string v2, "\u670d\u52a1\u5668\u70ed\u5207\u6362"

    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v4, v1}, Landroid/widget/Button;->setText(Ljava/lang/CharSequence;)V

    .line 1259
    new-instance v1, Lcom/android/support/Menu$20;

    invoke-direct {v1, p0, v0, v4}, Lcom/android/support/Menu$20;-><init>(Lcom/android/support/Menu;Landroid/widget/LinearLayout;Landroid/widget/Button;)V

    invoke-virtual {v4, v1}, Landroid/widget/Button;->setOnClickListener(Landroid/view/View$OnClickListener;)V

    .line 1267
    new-instance v1, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v2, -0x1

    const/4 v3, -0x2

    invoke-direct {v1, v2, v3}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    invoke-virtual {p1, v4, v1}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 1268
    new-instance v1, Landroid/widget/LinearLayout$LayoutParams;

    invoke-direct {v1, v2, v3}, Landroid/widget/LinearLayout$LayoutParams;-><init>(II)V

    invoke-virtual {p1, v0, v1}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 1269
    return-object v0
.end method

.method private applyUiScale(I)V
    .locals 4
    .param p1, "percent"    # I

    .line 700
    int-to-float v0, p1

    const/high16 v1, 0x42c80000    # 100.0f

    div-float/2addr v0, v1

    const v1, 0x3fb33333    # 1.4f

    invoke-static {v1, v0}, Ljava/lang/Math;->min(FF)F

    move-result v0

    const v1, 0x3f19999a    # 0.6f

    invoke-static {v1, v0}, Ljava/lang/Math;->max(FF)F

    move-result v0

    .line 701
    .local v0, "value":F
    :try_start_0
    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-static {v1}, Lcom/android/support/Preferences;->with(Landroid/content/Context;)Lcom/android/support/Preferences;

    move-result-object v1

    const-string v2, "uiScale"

    invoke-virtual {v1, v2, v0}, Lcom/android/support/Preferences;->writeFloat(Ljava/lang/String;F)V
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_0

    :catch_0
    move-exception v1

    .line 702
    :goto_0
    iput v0, p0, Lcom/android/support/Menu;->uiScale:F

    .line 704
    :try_start_1
    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    iget-object v2, p0, Lcom/android/support/Menu;->mTitle:Landroid/widget/TextView;

    iget-object v3, p0, Lcom/android/support/Menu;->mSubTitle:Landroid/widget/TextView;

    invoke-virtual {p0, v1, v2, v3}, Lcom/android/support/Menu;->Init(Landroid/content/Context;Landroid/widget/TextView;Landroid/widget/TextView;)V

    .line 705
    iget-object v1, p0, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-virtual {v1}, Landroid/widget/LinearLayout;->removeAllViews()V

    .line 706
    invoke-virtual {p0}, Lcom/android/support/Menu;->GetFeatureList()[Ljava/lang/String;

    move-result-object v1

    iget-object v2, p0, Lcom/android/support/Menu;->mods:Landroid/widget/LinearLayout;

    invoke-direct {p0, v1, v2}, Lcom/android/support/Menu;->featureList([Ljava/lang/String;Landroid/widget/LinearLayout;)V

    .line 707
    iget-object v1, p0, Lcom/android/support/Menu;->mSettings:Landroid/widget/LinearLayout;

    invoke-virtual {v1}, Landroid/widget/LinearLayout;->removeAllViews()V

    .line 708
    invoke-virtual {p0}, Lcom/android/support/Menu;->SettingsList()[Ljava/lang/String;

    move-result-object v1

    iget-object v2, p0, Lcom/android/support/Menu;->mSettings:Landroid/widget/LinearLayout;

    invoke-direct {p0, v1, v2}, Lcom/android/support/Menu;->featureList([Ljava/lang/String;Landroid/widget/LinearLayout;)V
    :try_end_1
    .catch Ljava/lang/Exception; {:try_start_1 .. :try_end_1} :catch_1

    goto :goto_1

    .line 709
    :catch_1
    move-exception v1

    :goto_1
    nop

    .line 710
    return-void
.end method

.method private convertDipToPixels(I)I
    .locals 2
    .param p1, "i"    # I

    .line 1370
    int-to-float v0, p1

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-virtual {v1}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    move-result-object v1

    invoke-virtual {v1}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    move-result-object v1

    iget v1, v1, Landroid/util/DisplayMetrics;->density:F

    mul-float v0, v0, v1

    const/high16 v1, 0x3f000000    # 0.5f

    add-float/2addr v0, v1

    float-to-int v0, v0

    return v0
.end method

.method private dp(I)I
    .locals 3
    .param p1, "i"    # I

    .line 1382
    int-to-float v0, p1

    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-virtual {v1}, Landroid/content/Context;->getResources()Landroid/content/res/Resources;

    move-result-object v1

    invoke-virtual {v1}, Landroid/content/res/Resources;->getDisplayMetrics()Landroid/util/DisplayMetrics;

    move-result-object v1

    const/4 v2, 0x1

    invoke-static {v2, v0, v1}, Landroid/util/TypedValue;->applyDimension(IFLandroid/util/DisplayMetrics;)F

    move-result v0

    float-to-int v0, v0

    return v0
.end method

.method private featureList([Ljava/lang/String;Landroid/widget/LinearLayout;)V
    .locals 23
    .param p1, "listFT"    # [Ljava/lang/String;
    .param p2, "linearLayout"    # Landroid/widget/LinearLayout;

    .line 502
    move-object/from16 v7, p0

    move-object/from16 v8, p1

    const/4 v1, 0x0

    .line 503
    .local v1, "subFeat":I
    move-object/from16 v9, p2

    .line 505
    .local v9, "llBak":Landroid/widget/LinearLayout;
    const/4 v2, 0x0

    .line 506
    .local v2, "hotSwitchBox":Landroid/widget/LinearLayout;
    const/4 v3, 0x0

    .line 507
    .local v3, "hotOpen":Z
    const/4 v10, 0x0

    :try_start_0
    iget-object v0, v7, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-static {v0}, Lcom/android/support/Preferences;->with(Landroid/content/Context;)Lcom/android/support/Preferences;

    move-result-object v0

    const-string v4, "hotSwitchOpen"

    invoke-virtual {v0, v4, v10}, Lcom/android/support/Preferences;->readBoolean(Ljava/lang/String;Z)Z

    move-result v0
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    move v3, v0

    goto :goto_0

    :catch_0
    move-exception v0

    move v0, v3

    .line 509
    .end local v3    # "hotOpen":Z
    .local v0, "hotOpen":Z
    :goto_0
    const/4 v3, 0x0

    move-object v11, v2

    move v12, v3

    move v2, v1

    move-object/from16 v1, p2

    .end local p2    # "linearLayout":Landroid/widget/LinearLayout;
    .local v1, "linearLayout":Landroid/widget/LinearLayout;
    .local v2, "subFeat":I
    .local v11, "hotSwitchBox":Landroid/widget/LinearLayout;
    .local v12, "i":I
    :goto_1
    array-length v3, v8

    if-ge v12, v3, :cond_b

    .line 510
    const/4 v3, 0x0

    .line 512
    .local v3, "switchedOn":Z
    aget-object v4, v8, v12

    .line 513
    .local v4, "feature":Ljava/lang/String;
    const-string v5, "_True"

    invoke-virtual {v4, v5}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v6

    const-string v13, ""

    if-eqz v6, :cond_0

    .line 514
    const/4 v3, 0x1

    .line 515
    invoke-virtual {v4, v5, v13}, Ljava/lang/String;->replaceFirst(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v4

    move v14, v3

    goto :goto_2

    .line 513
    :cond_0
    move v14, v3

    .line 518
    .end local v3    # "switchedOn":Z
    .local v14, "switchedOn":Z
    :goto_2
    move-object v1, v9

    .line 519
    const-string v3, "CollapseAdd_"

    invoke-virtual {v4, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v5

    if-eqz v5, :cond_1

    .line 521
    iget-object v1, v7, Lcom/android/support/Menu;->mCollapse:Landroid/widget/LinearLayout;

    .line 522
    invoke-virtual {v4, v3, v13}, Ljava/lang/String;->replaceFirst(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v4

    .line 524
    :cond_1
    const-string v3, "_"

    invoke-virtual {v4, v3}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;

    move-result-object v15

    .line 527
    .local v15, "str":[Ljava/lang/String;
    aget-object v5, v15, v10

    invoke-static {v5}, Landroid/text/TextUtils;->isDigitsOnly(Ljava/lang/CharSequence;)Z

    move-result v5

    if-nez v5, :cond_3

    aget-object v5, v15, v10

    const-string v6, "-[0-9]*"

    invoke-virtual {v5, v6}, Ljava/lang/String;->matches(Ljava/lang/String;)Z

    move-result v5

    if-eqz v5, :cond_2

    goto :goto_3

    .line 533
    :cond_2
    sub-int v5, v12, v2

    move v13, v2

    move v6, v5

    move-object v5, v4

    .local v5, "featNum":I
    goto :goto_4

    .line 528
    .end local v5    # "featNum":I
    :cond_3
    :goto_3
    aget-object v5, v15, v10

    invoke-static {v5}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I

    move-result v5

    .line 529
    .restart local v5    # "featNum":I
    new-instance v6, Ljava/lang/StringBuilder;

    invoke-direct {v6}, Ljava/lang/StringBuilder;-><init>()V

    move/from16 p2, v5

    .end local v5    # "featNum":I
    .local p2, "featNum":I
    aget-object v5, v15, v10

    invoke-virtual {v6, v5}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v5

    invoke-virtual {v5, v3}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    move-result-object v5

    invoke-virtual {v5}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v5

    invoke-virtual {v4, v5, v13}, Ljava/lang/String;->replaceFirst(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;

    move-result-object v4

    .line 530
    add-int/lit8 v2, v2, 0x1

    move/from16 v6, p2

    move v13, v2

    move-object v5, v4

    .line 535
    .end local v2    # "subFeat":I
    .end local v4    # "feature":Ljava/lang/String;
    .end local p2    # "featNum":I
    .local v5, "feature":Ljava/lang/String;
    .local v6, "featNum":I
    .local v13, "subFeat":I
    :goto_4
    invoke-virtual {v5, v3}, Ljava/lang/String;->split(Ljava/lang/String;)[Ljava/lang/String;

    move-result-object v4

    .line 537
    .local v4, "strSplit":[Ljava/lang/String;
    const/4 v2, 0x7

    if-eqz v11, :cond_4

    if-lt v6, v2, :cond_4

    const/16 v3, 0x10

    if-gt v6, v3, :cond_4

    if-ne v1, v9, :cond_4

    .line 538
    move-object v1, v11

    move-object v3, v1

    goto :goto_5

    .line 540
    :cond_4
    move-object v3, v1

    .end local v1    # "linearLayout":Landroid/widget/LinearLayout;
    .local v3, "linearLayout":Landroid/widget/LinearLayout;
    :goto_5
    aget-object v1, v4, v10

    invoke-virtual {v1}, Ljava/lang/String;->hashCode()I

    move-result v16

    const/4 v2, 0x1

    sparse-switch v16, :sswitch_data_0

    :cond_5
    goto/16 :goto_6

    :sswitch_0
    const-string v10, "Button"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/4 v1, 0x2

    goto/16 :goto_7

    :sswitch_1
    const-string v10, "CheckBox"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/16 v1, 0x8

    goto/16 :goto_7

    :sswitch_2
    const-string v10, "InputLValue"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/4 v1, 0x7

    goto/16 :goto_7

    :sswitch_3
    const-string v10, "RadioButton"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/16 v1, 0x9

    goto/16 :goto_7

    :sswitch_4
    const-string v10, "RichWebView"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/16 v1, 0xe

    goto/16 :goto_7

    :sswitch_5
    const-string v10, "Category"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/16 v1, 0xc

    goto :goto_7

    :sswitch_6
    const-string v10, "RichTextView"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/16 v1, 0xd

    goto :goto_7

    :sswitch_7
    const-string v10, "ButtonOnOff"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/4 v1, 0x3

    goto :goto_7

    :sswitch_8
    const-string v10, "Spinner"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/4 v1, 0x4

    goto :goto_7

    :sswitch_9
    const-string v10, "Collapse"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/16 v1, 0xa

    goto :goto_7

    :sswitch_a
    const-string v10, "InputText"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/4 v1, 0x5

    goto :goto_7

    :sswitch_b
    const-string v10, "SeekBar"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/4 v1, 0x1

    goto :goto_7

    :sswitch_c
    const-string v10, "InputValue"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/4 v1, 0x6

    goto :goto_7

    :sswitch_d
    const-string v10, "Toggle"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/4 v1, 0x0

    goto :goto_7

    :sswitch_e
    const-string v10, "ButtonLink"

    invoke-virtual {v1, v10}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z

    move-result v1

    if-eqz v1, :cond_5

    const/16 v1, 0xb

    goto :goto_7

    :goto_6
    const/4 v1, -0x1

    :goto_7
    packed-switch v1, :pswitch_data_0

    move/from16 v21, v0

    move-object v8, v3

    move-object v0, v4

    move-object v10, v5

    move-object/from16 v16, v9

    const/16 v19, 0x0

    move v9, v6

    .end local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v4    # "strSplit":[Ljava/lang/String;
    .end local v5    # "feature":Ljava/lang/String;
    .end local v6    # "featNum":I
    .local v0, "strSplit":[Ljava/lang/String;
    .local v8, "linearLayout":Landroid/widget/LinearLayout;
    .local v9, "featNum":I
    .local v10, "feature":Ljava/lang/String;
    .local v16, "llBak":Landroid/widget/LinearLayout;
    .local v21, "hotOpen":Z
    goto/16 :goto_a

    .line 599
    .end local v8    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v10    # "feature":Ljava/lang/String;
    .end local v16    # "llBak":Landroid/widget/LinearLayout;
    .end local v21    # "hotOpen":Z
    .local v0, "hotOpen":Z
    .restart local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v4    # "strSplit":[Ljava/lang/String;
    .restart local v5    # "feature":Ljava/lang/String;
    .restart local v6    # "featNum":I
    .local v9, "llBak":Landroid/widget/LinearLayout;
    :pswitch_0
    add-int/lit8 v13, v13, 0x1

    .line 600
    aget-object v1, v4, v2

    invoke-direct {v7, v3, v1}, Lcom/android/support/Menu;->WebTextView(Landroid/widget/LinearLayout;Ljava/lang/String;)V

    move/from16 v21, v0

    move-object v8, v3

    move-object/from16 v16, v9

    move v2, v13

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_b

    .line 595
    :pswitch_1
    add-int/lit8 v13, v13, 0x1

    .line 596
    aget-object v1, v4, v2

    invoke-direct {v7, v3, v1}, Lcom/android/support/Menu;->TextView(Landroid/widget/LinearLayout;Ljava/lang/String;)V

    .line 597
    move/from16 v21, v0

    move-object v8, v3

    move-object/from16 v16, v9

    move v2, v13

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_b

    .line 587
    :pswitch_2
    add-int/lit8 v13, v13, 0x1

    .line 588
    array-length v1, v4

    if-le v1, v2, :cond_6

    aget-object v1, v4, v2

    const-string v10, "\u670d\u52a1\u5668\u70ed\u5207\u6362"

    invoke-virtual {v1, v10}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v1

    if-eqz v1, :cond_6

    .line 589
    invoke-direct {v7, v3, v0}, Lcom/android/support/Menu;->addHotSwitchHeader(Landroid/widget/LinearLayout;Z)Landroid/widget/LinearLayout;

    move-result-object v1

    .line 590
    .end local v11    # "hotSwitchBox":Landroid/widget/LinearLayout;
    .local v1, "hotSwitchBox":Landroid/widget/LinearLayout;
    move/from16 v21, v0

    move-object v11, v1

    move-object v8, v3

    move-object/from16 v16, v9

    move v2, v13

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_b

    .line 592
    .end local v1    # "hotSwitchBox":Landroid/widget/LinearLayout;
    .restart local v11    # "hotSwitchBox":Landroid/widget/LinearLayout;
    :cond_6
    aget-object v1, v4, v2

    invoke-direct {v7, v3, v1}, Lcom/android/support/Menu;->Category(Landroid/widget/LinearLayout;Ljava/lang/String;)V

    .line 593
    move/from16 v21, v0

    move-object v8, v3

    move-object/from16 v16, v9

    move v2, v13

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_b

    .line 583
    :pswitch_3
    add-int/lit8 v13, v13, 0x1

    .line 584
    aget-object v1, v4, v2

    const/4 v2, 0x2

    aget-object v2, v4, v2

    invoke-direct {v7, v3, v1, v2}, Lcom/android/support/Menu;->ButtonLink(Landroid/widget/LinearLayout;Ljava/lang/String;Ljava/lang/String;)V

    .line 585
    move/from16 v21, v0

    move-object v8, v3

    move-object/from16 v16, v9

    move v2, v13

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_b

    .line 579
    :pswitch_4
    aget-object v1, v4, v2

    invoke-direct {v7, v3, v1, v14}, Lcom/android/support/Menu;->Collapse(Landroid/widget/LinearLayout;Ljava/lang/String;Z)V

    .line 580
    add-int/lit8 v13, v13, 0x1

    .line 581
    move/from16 v21, v0

    move-object v8, v3

    move-object/from16 v16, v9

    move v2, v13

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_b

    .line 576
    :pswitch_5
    aget-object v1, v4, v2

    const/4 v2, 0x2

    aget-object v2, v4, v2

    invoke-direct {v7, v3, v6, v1, v2}, Lcom/android/support/Menu;->RadioButton(Landroid/widget/LinearLayout;ILjava/lang/String;Ljava/lang/String;)V

    .line 577
    move/from16 v21, v0

    move-object v8, v3

    move-object/from16 v16, v9

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_a

    .line 573
    :pswitch_6
    aget-object v1, v4, v2

    invoke-direct {v7, v3, v6, v1, v14}, Lcom/android/support/Menu;->CheckBox(Landroid/widget/LinearLayout;ILjava/lang/String;Z)V

    .line 574
    move/from16 v21, v0

    move-object v8, v3

    move-object/from16 v16, v9

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_a

    .line 567
    :pswitch_7
    array-length v1, v4

    const/4 v10, 0x3

    if-ne v1, v10, :cond_7

    .line 568
    const/4 v1, 0x2

    aget-object v10, v4, v1

    aget-object v1, v4, v2

    invoke-static {v1}, Ljava/lang/Long;->parseLong(Ljava/lang/String;)J

    move-result-wide v18

    move-object/from16 v1, p0

    const/16 v20, 0x1

    move-object v2, v3

    move-object/from16 p2, v3

    .end local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .local p2, "linearLayout":Landroid/widget/LinearLayout;
    move v3, v6

    move/from16 v21, v0

    move-object v0, v4

    .end local v4    # "strSplit":[Ljava/lang/String;
    .local v0, "strSplit":[Ljava/lang/String;
    .restart local v21    # "hotOpen":Z
    move-object v4, v10

    move-object v10, v5

    move/from16 v22, v6

    .end local v5    # "feature":Ljava/lang/String;
    .end local v6    # "featNum":I
    .restart local v10    # "feature":Ljava/lang/String;
    .local v22, "featNum":I
    move-wide/from16 v5, v18

    invoke-direct/range {v1 .. v6}, Lcom/android/support/Menu;->InputLNum(Landroid/widget/LinearLayout;ILjava/lang/String;J)V

    goto :goto_8

    .line 567
    .end local v10    # "feature":Ljava/lang/String;
    .end local v21    # "hotOpen":Z
    .end local v22    # "featNum":I
    .end local p2    # "linearLayout":Landroid/widget/LinearLayout;
    .local v0, "hotOpen":Z
    .restart local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v4    # "strSplit":[Ljava/lang/String;
    .restart local v5    # "feature":Ljava/lang/String;
    .restart local v6    # "featNum":I
    :cond_7
    move/from16 v21, v0

    move-object/from16 p2, v3

    move-object v0, v4

    move-object v10, v5

    move/from16 v22, v6

    const/16 v20, 0x1

    .line 569
    .end local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v4    # "strSplit":[Ljava/lang/String;
    .end local v5    # "feature":Ljava/lang/String;
    .end local v6    # "featNum":I
    .local v0, "strSplit":[Ljava/lang/String;
    .restart local v10    # "feature":Ljava/lang/String;
    .restart local v21    # "hotOpen":Z
    .restart local v22    # "featNum":I
    .restart local p2    # "linearLayout":Landroid/widget/LinearLayout;
    :goto_8
    array-length v1, v0

    const/4 v2, 0x2

    if-ne v1, v2, :cond_8

    .line 570
    aget-object v4, v0, v20

    const-wide/16 v5, 0x0

    move-object/from16 v1, p0

    move-object/from16 v2, p2

    move/from16 v3, v22

    invoke-direct/range {v1 .. v6}, Lcom/android/support/Menu;->InputLNum(Landroid/widget/LinearLayout;ILjava/lang/String;J)V

    move-object/from16 v8, p2

    move-object/from16 v16, v9

    move/from16 v9, v22

    const/16 v19, 0x0

    goto/16 :goto_a

    .line 569
    :cond_8
    move-object/from16 v8, p2

    move-object/from16 v16, v9

    move/from16 v9, v22

    const/16 v19, 0x0

    goto/16 :goto_a

    .line 561
    .end local v10    # "feature":Ljava/lang/String;
    .end local v21    # "hotOpen":Z
    .end local v22    # "featNum":I
    .end local p2    # "linearLayout":Landroid/widget/LinearLayout;
    .local v0, "hotOpen":Z
    .restart local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v4    # "strSplit":[Ljava/lang/String;
    .restart local v5    # "feature":Ljava/lang/String;
    .restart local v6    # "featNum":I
    :pswitch_8
    move/from16 v21, v0

    move-object/from16 p2, v3

    move-object v0, v4

    move-object v10, v5

    move/from16 v22, v6

    const/16 v20, 0x1

    .end local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v4    # "strSplit":[Ljava/lang/String;
    .end local v5    # "feature":Ljava/lang/String;
    .end local v6    # "featNum":I
    .local v0, "strSplit":[Ljava/lang/String;
    .restart local v10    # "feature":Ljava/lang/String;
    .restart local v21    # "hotOpen":Z
    .restart local v22    # "featNum":I
    .restart local p2    # "linearLayout":Landroid/widget/LinearLayout;
    array-length v1, v0

    const/4 v2, 0x3

    if-ne v1, v2, :cond_9

    .line 562
    const/4 v1, 0x2

    aget-object v2, v0, v1

    aget-object v3, v0, v20

    invoke-static {v3}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I

    move-result v3

    move-object/from16 v5, p2

    move/from16 v6, v22

    .end local v22    # "featNum":I
    .end local p2    # "linearLayout":Landroid/widget/LinearLayout;
    .local v5, "linearLayout":Landroid/widget/LinearLayout;
    .restart local v6    # "featNum":I
    invoke-direct {v7, v5, v6, v2, v3}, Lcom/android/support/Menu;->InputNum(Landroid/widget/LinearLayout;ILjava/lang/String;I)V

    goto :goto_9

    .line 561
    .end local v5    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v6    # "featNum":I
    .restart local v22    # "featNum":I
    .restart local p2    # "linearLayout":Landroid/widget/LinearLayout;
    :cond_9
    move-object/from16 v5, p2

    move/from16 v6, v22

    const/4 v1, 0x2

    .line 563
    .end local v22    # "featNum":I
    .end local p2    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v5    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v6    # "featNum":I
    :goto_9
    array-length v2, v0

    if-ne v2, v1, :cond_a

    .line 564
    aget-object v1, v0, v20

    const/4 v4, 0x0

    invoke-direct {v7, v5, v6, v1, v4}, Lcom/android/support/Menu;->InputNum(Landroid/widget/LinearLayout;ILjava/lang/String;I)V

    move-object v8, v5

    move-object/from16 v16, v9

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_a

    .line 563
    :cond_a
    const/4 v4, 0x0

    move-object v8, v5

    move-object/from16 v16, v9

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_a

    .line 558
    .end local v10    # "feature":Ljava/lang/String;
    .end local v21    # "hotOpen":Z
    .local v0, "hotOpen":Z
    .restart local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v4    # "strSplit":[Ljava/lang/String;
    .local v5, "feature":Ljava/lang/String;
    :pswitch_9
    move/from16 v21, v0

    move-object v0, v4

    move-object v10, v5

    const/4 v4, 0x0

    const/16 v20, 0x1

    move-object v5, v3

    .end local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v4    # "strSplit":[Ljava/lang/String;
    .local v0, "strSplit":[Ljava/lang/String;
    .local v5, "linearLayout":Landroid/widget/LinearLayout;
    .restart local v10    # "feature":Ljava/lang/String;
    .restart local v21    # "hotOpen":Z
    aget-object v1, v0, v20

    invoke-direct {v7, v5, v6, v1}, Lcom/android/support/Menu;->InputText(Landroid/widget/LinearLayout;ILjava/lang/String;)V

    .line 559
    move-object v8, v5

    move-object/from16 v16, v9

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_a

    .line 554
    .end local v10    # "feature":Ljava/lang/String;
    .end local v21    # "hotOpen":Z
    .local v0, "hotOpen":Z
    .restart local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v4    # "strSplit":[Ljava/lang/String;
    .local v5, "feature":Ljava/lang/String;
    :pswitch_a
    move/from16 v21, v0

    move-object v0, v4

    move-object v10, v5

    const/4 v4, 0x0

    const/16 v20, 0x1

    move-object v5, v3

    .end local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v4    # "strSplit":[Ljava/lang/String;
    .local v0, "strSplit":[Ljava/lang/String;
    .local v5, "linearLayout":Landroid/widget/LinearLayout;
    .restart local v10    # "feature":Ljava/lang/String;
    .restart local v21    # "hotOpen":Z
    aget-object v1, v0, v20

    invoke-direct {v7, v5, v1}, Lcom/android/support/Menu;->TextView(Landroid/widget/LinearLayout;Ljava/lang/String;)V

    .line 555
    aget-object v1, v0, v20

    const/4 v2, 0x2

    aget-object v2, v0, v2

    invoke-direct {v7, v5, v6, v1, v2}, Lcom/android/support/Menu;->Spinner(Landroid/widget/LinearLayout;ILjava/lang/String;Ljava/lang/String;)V

    .line 556
    move-object v8, v5

    move-object/from16 v16, v9

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_a

    .line 551
    .end local v10    # "feature":Ljava/lang/String;
    .end local v21    # "hotOpen":Z
    .local v0, "hotOpen":Z
    .restart local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v4    # "strSplit":[Ljava/lang/String;
    .local v5, "feature":Ljava/lang/String;
    :pswitch_b
    move/from16 v21, v0

    move-object v0, v4

    move-object v10, v5

    const/4 v4, 0x0

    const/16 v20, 0x1

    move-object v5, v3

    .end local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v4    # "strSplit":[Ljava/lang/String;
    .local v0, "strSplit":[Ljava/lang/String;
    .local v5, "linearLayout":Landroid/widget/LinearLayout;
    .restart local v10    # "feature":Ljava/lang/String;
    .restart local v21    # "hotOpen":Z
    aget-object v1, v0, v20

    invoke-direct {v7, v5, v6, v1, v14}, Lcom/android/support/Menu;->ButtonOnOff(Landroid/widget/LinearLayout;ILjava/lang/String;Z)V

    .line 552
    move-object v8, v5

    move-object/from16 v16, v9

    const/16 v19, 0x0

    move v9, v6

    goto/16 :goto_a

    .line 548
    .end local v10    # "feature":Ljava/lang/String;
    .end local v21    # "hotOpen":Z
    .local v0, "hotOpen":Z
    .restart local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v4    # "strSplit":[Ljava/lang/String;
    .local v5, "feature":Ljava/lang/String;
    :pswitch_c
    move/from16 v21, v0

    move-object v0, v4

    move-object v10, v5

    const/4 v4, 0x0

    const/16 v20, 0x1

    move-object v5, v3

    .end local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v4    # "strSplit":[Ljava/lang/String;
    .local v0, "strSplit":[Ljava/lang/String;
    .local v5, "linearLayout":Landroid/widget/LinearLayout;
    .restart local v10    # "feature":Ljava/lang/String;
    .restart local v21    # "hotOpen":Z
    aget-object v1, v0, v20

    invoke-direct {v7, v5, v6, v1}, Lcom/android/support/Menu;->Button(Landroid/widget/LinearLayout;ILjava/lang/String;)V

    .line 549
    move-object v8, v5

    move-object/from16 v16, v9

    const/16 v19, 0x0

    move v9, v6

    goto :goto_a

    .line 545
    .end local v10    # "feature":Ljava/lang/String;
    .end local v21    # "hotOpen":Z
    .local v0, "hotOpen":Z
    .restart local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v4    # "strSplit":[Ljava/lang/String;
    .local v5, "feature":Ljava/lang/String;
    :pswitch_d
    move/from16 v21, v0

    move-object v0, v4

    move-object v10, v5

    const/4 v4, 0x0

    const/16 v20, 0x1

    move-object v5, v3

    .end local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v4    # "strSplit":[Ljava/lang/String;
    .local v0, "strSplit":[Ljava/lang/String;
    .local v5, "linearLayout":Landroid/widget/LinearLayout;
    .restart local v10    # "feature":Ljava/lang/String;
    .restart local v21    # "hotOpen":Z
    aget-object v17, v0, v20

    const/4 v1, 0x2

    aget-object v1, v0, v1

    invoke-static {v1}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I

    move-result v16

    const/4 v1, 0x3

    aget-object v1, v0, v1

    invoke-static {v1}, Ljava/lang/Integer;->parseInt(Ljava/lang/String;)I

    move-result v18

    move-object/from16 v1, p0

    move-object v2, v5

    move v3, v6

    const/16 v19, 0x0

    move-object/from16 v4, v17

    move-object v8, v5

    .end local v5    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v8    # "linearLayout":Landroid/widget/LinearLayout;
    move/from16 v5, v16

    move-object/from16 v16, v9

    move v9, v6

    .end local v6    # "featNum":I
    .local v9, "featNum":I
    .restart local v16    # "llBak":Landroid/widget/LinearLayout;
    move/from16 v6, v18

    invoke-direct/range {v1 .. v6}, Lcom/android/support/Menu;->SeekBar(Landroid/widget/LinearLayout;ILjava/lang/String;II)V

    .line 546
    goto :goto_a

    .line 542
    .end local v8    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v10    # "feature":Ljava/lang/String;
    .end local v16    # "llBak":Landroid/widget/LinearLayout;
    .end local v21    # "hotOpen":Z
    .local v0, "hotOpen":Z
    .restart local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .restart local v4    # "strSplit":[Ljava/lang/String;
    .local v5, "feature":Ljava/lang/String;
    .restart local v6    # "featNum":I
    .local v9, "llBak":Landroid/widget/LinearLayout;
    :pswitch_e
    move/from16 v21, v0

    move-object v8, v3

    move-object v0, v4

    move-object v10, v5

    move-object/from16 v16, v9

    const/16 v19, 0x0

    const/16 v20, 0x1

    move v9, v6

    .end local v3    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v4    # "strSplit":[Ljava/lang/String;
    .end local v5    # "feature":Ljava/lang/String;
    .end local v6    # "featNum":I
    .local v0, "strSplit":[Ljava/lang/String;
    .restart local v8    # "linearLayout":Landroid/widget/LinearLayout;
    .local v9, "featNum":I
    .restart local v10    # "feature":Ljava/lang/String;
    .restart local v16    # "llBak":Landroid/widget/LinearLayout;
    .restart local v21    # "hotOpen":Z
    aget-object v1, v0, v20

    invoke-direct {v7, v8, v9, v1, v14}, Lcom/android/support/Menu;->Switch(Landroid/widget/LinearLayout;ILjava/lang/String;Z)V

    .line 543
    nop

    .line 509
    .end local v0    # "strSplit":[Ljava/lang/String;
    .end local v10    # "feature":Ljava/lang/String;
    .end local v14    # "switchedOn":Z
    .end local v15    # "str":[Ljava/lang/String;
    :goto_a
    move v2, v13

    .end local v13    # "subFeat":I
    .restart local v2    # "subFeat":I
    :goto_b
    add-int/lit8 v12, v12, 0x1

    move-object v1, v8

    move-object/from16 v9, v16

    move/from16 v0, v21

    const/4 v10, 0x0

    move-object/from16 v8, p1

    goto/16 :goto_1

    .line 604
    .end local v8    # "linearLayout":Landroid/widget/LinearLayout;
    .end local v12    # "i":I
    .end local v16    # "llBak":Landroid/widget/LinearLayout;
    .end local v21    # "hotOpen":Z
    .local v0, "hotOpen":Z
    .local v1, "linearLayout":Landroid/widget/LinearLayout;
    .local v9, "llBak":Landroid/widget/LinearLayout;
    :cond_b
    return-void

    nop

    :sswitch_data_0
    .sparse-switch
        -0x73d2c194 -> :sswitch_e
        -0x6a5c588c -> :sswitch_d
        -0x370e8c19 -> :sswitch_c
        -0x274065a5 -> :sswitch_b
        -0x22cfc409 -> :sswitch_a
        -0x21d27833 -> :sswitch_9
        -0x1440b607 -> :sswitch_8
        -0x6595922 -> :sswitch_7
        0x4f11a8e -> :sswitch_6
        0x6dd211e -> :sswitch_5
        0x1977177d -> :sswitch_4
        0x2e46a6ed -> :sswitch_3
        0x438c70af -> :sswitch_2
        0x5f7507c3 -> :sswitch_1
        0x77471352 -> :sswitch_0
    .end sparse-switch

    :pswitch_data_0
    .packed-switch 0x0
        :pswitch_e
        :pswitch_d
        :pswitch_c
        :pswitch_b
        :pswitch_a
        :pswitch_9
        :pswitch_8
        :pswitch_7
        :pswitch_6
        :pswitch_5
        :pswitch_4
        :pswitch_3
        :pswitch_2
        :pswitch_1
        :pswitch_0
    .end packed-switch
.end method

.method private isViewCollapsed()Z
    .locals 1

    .line 1365
    iget-object v0, p0, Lcom/android/support/Menu;->rootFrame:Landroid/widget/FrameLayout;

    if-eqz v0, :cond_1

    iget-object v0, p0, Lcom/android/support/Menu;->mCollapsed:Landroid/widget/RelativeLayout;

    invoke-virtual {v0}, Landroid/widget/RelativeLayout;->getVisibility()I

    move-result v0

    if-nez v0, :cond_0

    goto :goto_0

    :cond_0
    const/4 v0, 0x0

    goto :goto_1

    :cond_1
    :goto_0
    const/4 v0, 0x1

    :goto_1
    return v0
.end method

.method private loadUiScale()V
    .locals 4

    .line 85
    const/high16 v0, 0x3f800000    # 1.0f

    :try_start_0
    iget-object v1, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-static {v1}, Lcom/android/support/Preferences;->with(Landroid/content/Context;)Lcom/android/support/Preferences;

    move-result-object v1

    const-string v2, "uiScale"

    invoke-virtual {v1, v2, v0}, Lcom/android/support/Preferences;->readFloat(Ljava/lang/String;F)F

    move-result v1

    .line 86
    .local v1, "v":F
    const v2, 0x3fb33333    # 1.4f

    invoke-static {v2, v1}, Ljava/lang/Math;->min(FF)F

    move-result v2

    const v3, 0x3f19999a    # 0.6f

    invoke-static {v3, v2}, Ljava/lang/Math;->max(FF)F

    move-result v2

    iput v2, p0, Lcom/android/support/Menu;->uiScale:F
    :try_end_0
    .catch Ljava/lang/Exception; {:try_start_0 .. :try_end_0} :catch_0

    .line 89
    .end local v1    # "v":F
    goto :goto_0

    .line 87
    :catch_0
    move-exception v1

    .line 88
    .local v1, "e":Ljava/lang/Exception;
    iput v0, p0, Lcom/android/support/Menu;->uiScale:F

    .line 90
    .end local v1    # "e":Ljava/lang/Exception;
    :goto_0
    return-void
.end method

.method private onTouchListener()Landroid/view/View$OnTouchListener;
    .locals 1

    .line 451
    new-instance v0, Lcom/android/support/Menu$7;

    invoke-direct {v0, p0}, Lcom/android/support/Menu$7;-><init>(Lcom/android/support/Menu;)V

    return-object v0
.end method

.method private panel(II)Landroid/graphics/drawable/GradientDrawable;
    .locals 3
    .param p1, "fill"    # I
    .param p2, "strokeDp"    # I

    .line 1348
    new-instance v0, Landroid/graphics/drawable/GradientDrawable;

    invoke-direct {v0}, Landroid/graphics/drawable/GradientDrawable;-><init>()V

    .line 1349
    .local v0, "drawable":Landroid/graphics/drawable/GradientDrawable;
    invoke-virtual {v0, p1}, Landroid/graphics/drawable/GradientDrawable;->setColor(I)V

    .line 1350
    iget v1, p0, Lcom/android/support/Menu;->CARD_RADIUS:I

    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v1

    int-to-float v1, v1

    invoke-virtual {v0, v1}, Landroid/graphics/drawable/GradientDrawable;->setCornerRadius(F)V

    .line 1351
    invoke-direct {p0, p2}, Lcom/android/support/Menu;->dp(I)I

    move-result v1

    iget v2, p0, Lcom/android/support/Menu;->BORDER_COLOR:I

    invoke-virtual {v0, v1, v2}, Landroid/graphics/drawable/GradientDrawable;->setStroke(II)V

    .line 1352
    return-object v0
.end method

.method private rect(II)Landroid/graphics/drawable/GradientDrawable;
    .locals 2
    .param p1, "fill"    # I
    .param p2, "stroke"    # I

    .line 1374
    new-instance v0, Landroid/graphics/drawable/GradientDrawable;

    invoke-direct {v0}, Landroid/graphics/drawable/GradientDrawable;-><init>()V

    .line 1375
    .local v0, "g":Landroid/graphics/drawable/GradientDrawable;
    iget v1, p0, Lcom/android/support/Menu;->MENU_CORNER:F

    invoke-virtual {v0, v1}, Landroid/graphics/drawable/GradientDrawable;->setCornerRadius(F)V

    .line 1376
    invoke-virtual {v0, p1}, Landroid/graphics/drawable/GradientDrawable;->setColor(I)V

    .line 1377
    const/4 v1, 0x1

    invoke-direct {p0, v1}, Lcom/android/support/Menu;->dp(I)I

    move-result v1

    invoke-virtual {v0, v1, p2}, Landroid/graphics/drawable/GradientDrawable;->setStroke(II)V

    .line 1378
    return-object v0
.end method

.method private setScaledTextSize(Landroid/widget/TextView;F)V
    .locals 1
    .param p1, "view"    # Landroid/widget/TextView;
    .param p2, "base"    # F

    .line 92
    iget v0, p0, Lcom/android/support/Menu;->uiScale:F

    mul-float v0, v0, p2

    invoke-virtual {p1, v0}, Landroid/widget/TextView;->setTextSize(F)V

    .line 93
    return-void
.end method

.method private statusRow(Landroid/widget/LinearLayout;Ljava/lang/String;)V
    .locals 12
    .param p1, "linLayout"    # Landroid/widget/LinearLayout;
    .param p2, "text"    # Ljava/lang/String;

    .line 1307
    const/16 v0, 0x3a

    invoke-virtual {p2, v0}, Ljava/lang/String;->indexOf(I)I

    move-result v0

    .line 1308
    .local v0, "colon":I
    const/4 v1, 0x0

    if-lez v0, :cond_0

    invoke-virtual {p2, v1, v0}, Ljava/lang/String;->substring(II)Ljava/lang/String;

    move-result-object v2

    goto :goto_0

    :cond_0
    move-object v2, p2

    .line 1309
    .local v2, "label":Ljava/lang/String;
    :goto_0
    if-lez v0, :cond_1

    add-int/lit8 v3, v0, 0x1

    invoke-virtual {p2, v3}, Ljava/lang/String;->substring(I)Ljava/lang/String;

    move-result-object v3

    invoke-virtual {v3}, Ljava/lang/String;->trim()Ljava/lang/String;

    move-result-object v3

    goto :goto_1

    :cond_1
    const-string v3, ""

    .line 1310
    .local v3, "value":Ljava/lang/String;
    :goto_1
    const-string v4, "\u7b49\u5f85"

    invoke-virtual {v3, v4}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v4

    const/4 v5, 0x1

    if-nez v4, :cond_2

    const-string v4, "OFF"

    invoke-virtual {v3, v4}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z

    move-result v4

    if-nez v4, :cond_2

    const-string v4, "0/"

    invoke-virtual {v3, v4}, Ljava/lang/String;->startsWith(Ljava/lang/String;)Z

    move-result v4

    if-nez v4, :cond_2

    invoke-virtual {v3}, Ljava/lang/String;->isEmpty()Z

    move-result v4

    if-nez v4, :cond_2

    const/4 v4, 0x1

    goto :goto_2

    :cond_2
    const/4 v4, 0x0

    .line 1312
    .local v4, "ok":Z
    :goto_2
    new-instance v6, Landroid/widget/LinearLayout;

    iget-object v7, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v6, v7}, Landroid/widget/LinearLayout;-><init>(Landroid/content/Context;)V

    .line 1313
    .local v6, "row":Landroid/widget/LinearLayout;
    invoke-virtual {v6, v1}, Landroid/widget/LinearLayout;->setOrientation(I)V

    .line 1314
    const/16 v7, 0x10

    invoke-virtual {v6, v7}, Landroid/widget/LinearLayout;->setGravity(I)V

    .line 1315
    const/16 v7, 0xc

    invoke-direct {p0, v7}, Lcom/android/support/Menu;->dp(I)I

    move-result v8

    const/4 v9, 0x5

    invoke-direct {p0, v9}, Lcom/android/support/Menu;->dp(I)I

    move-result v10

    invoke-direct {p0, v7}, Lcom/android/support/Menu;->dp(I)I

    move-result v7

    invoke-direct {p0, v9}, Lcom/android/support/Menu;->dp(I)I

    move-result v9

    invoke-virtual {v6, v8, v10, v7, v9}, Landroid/widget/LinearLayout;->setPadding(IIII)V

    .line 1317
    new-instance v7, Landroid/widget/TextView;

    iget-object v8, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v7, v8}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 1318
    .local v7, "name":Landroid/widget/TextView;
    invoke-virtual {v7, v2}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 1319
    iget v8, p0, Lcom/android/support/Menu;->INK:I

    invoke-virtual {v7, v8}, Landroid/widget/TextView;->setTextColor(I)V

    .line 1320
    sget-object v8, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v7, v8}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;)V

    .line 1321
    invoke-virtual {v7, v5}, Landroid/widget/TextView;->setAllCaps(Z)V

    .line 1322
    invoke-direct {p0, v7}, Lcom/android/support/Menu;->track(Landroid/widget/TextView;)V

    .line 1323
    const/high16 v8, 0x41300000    # 11.0f

    invoke-direct {p0, v7, v8}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 1324
    new-instance v9, Landroid/widget/LinearLayout$LayoutParams;

    const/4 v10, -0x2

    const/high16 v11, 0x3f800000    # 1.0f

    invoke-direct {v9, v1, v10, v11}, Landroid/widget/LinearLayout$LayoutParams;-><init>(IIF)V

    invoke-virtual {v6, v7, v9}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 1327
    new-instance v1, Landroid/widget/TextView;

    iget-object v9, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    invoke-direct {v1, v9}, Landroid/widget/TextView;-><init>(Landroid/content/Context;)V

    .line 1328
    .local v1, "chip":Landroid/widget/TextView;
    invoke-virtual {v1, v3}, Landroid/widget/TextView;->setText(Ljava/lang/CharSequence;)V

    .line 1329
    iget v9, p0, Lcom/android/support/Menu;->PAPER:I

    invoke-virtual {v1, v9}, Landroid/widget/TextView;->setTextColor(I)V

    .line 1330
    sget-object v9, Landroid/graphics/Typeface;->MONOSPACE:Landroid/graphics/Typeface;

    invoke-virtual {v1, v9, v5}, Landroid/widget/TextView;->setTypeface(Landroid/graphics/Typeface;I)V

    .line 1331
    invoke-direct {p0, v1}, Lcom/android/support/Menu;->track(Landroid/widget/TextView;)V

    .line 1332
    invoke-direct {p0, v1, v8}, Lcom/android/support/Menu;->setScaledTextSize(Landroid/widget/TextView;F)V

    .line 1333
    const/4 v8, 0x7

    invoke-direct {p0, v8}, Lcom/android/support/Menu;->dp(I)I

    move-result v9

    const/4 v10, 0x3

    invoke-direct {p0, v10}, Lcom/android/support/Menu;->dp(I)I

    move-result v11

    invoke-direct {p0, v8}, Lcom/android/support/Menu;->dp(I)I

    move-result v8

    invoke-direct {p0, v10}, Lcom/android/support/Menu;->dp(I)I

    move-result v10

    invoke-virtual {v1, v9, v11, v8, v10}, Landroid/widget/TextView;->setPadding(IIII)V

    .line 1334
    if-eqz v4, :cond_3

    iget v8, p0, Lcom/android/support/Menu;->STATUS_OK:I

    goto :goto_3

    :cond_3
    iget v8, p0, Lcom/android/support/Menu;->STATUS_ALERT:I

    :goto_3
    invoke-direct {p0, v8, v5}, Lcom/android/support/Menu;->panel(II)Landroid/graphics/drawable/GradientDrawable;

    move-result-object v5

    invoke-virtual {v1, v5}, Landroid/widget/TextView;->setBackground(Landroid/graphics/drawable/Drawable;)V

    .line 1335
    invoke-virtual {v6, v1}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1337
    invoke-virtual {p1, v6}, Landroid/widget/LinearLayout;->addView(Landroid/view/View;)V

    .line 1338
    return-void
.end method

.method private track(Landroid/widget/TextView;)V
    .locals 1
    .param p1, "view"    # Landroid/widget/TextView;

    .line 1342
    nop

    .line 1343
    iget v0, p0, Lcom/android/support/Menu;->TRACKING:F

    invoke-virtual {p1, v0}, Landroid/widget/TextView;->setLetterSpacing(F)V

    .line 1344
    return-void
.end method


# virtual methods
.method native GetFeatureList()[Ljava/lang/String;
.end method

.method native Icon()Ljava/lang/String;
.end method

.method native IconWebViewData()Ljava/lang/String;
.end method

.method native Init(Landroid/content/Context;Landroid/widget/TextView;Landroid/widget/TextView;)V
.end method

.method native IsGameLibLoaded()Z
.end method

.method public SetWindowManagerActivity()V
    .locals 9

    .line 430
    new-instance v8, Landroid/view/WindowManager$LayoutParams;

    iget v3, p0, Lcom/android/support/Menu;->POS_X:I

    iget v4, p0, Lcom/android/support/Menu;->POS_Y:I

    const v6, 0x2800108

    const/4 v7, -0x2

    const/4 v1, -0x2

    const/4 v2, -0x2

    const/4 v5, 0x2

    move-object v0, v8

    invoke-direct/range {v0 .. v7}, Landroid/view/WindowManager$LayoutParams;-><init>(IIIIIII)V

    iput-object v8, p0, Lcom/android/support/Menu;->vmParams:Landroid/view/WindowManager$LayoutParams;

    .line 442
    iget-object v0, p0, Lcom/android/support/Menu;->vmParams:Landroid/view/WindowManager$LayoutParams;

    const/16 v1, 0x33

    iput v1, v0, Landroid/view/WindowManager$LayoutParams;->gravity:I

    .line 443
    iget-object v0, p0, Lcom/android/support/Menu;->vmParams:Landroid/view/WindowManager$LayoutParams;

    iget v1, p0, Lcom/android/support/Menu;->POS_X:I

    iput v1, v0, Landroid/view/WindowManager$LayoutParams;->x:I

    .line 444
    iget-object v0, p0, Lcom/android/support/Menu;->vmParams:Landroid/view/WindowManager$LayoutParams;

    iget v1, p0, Lcom/android/support/Menu;->POS_Y:I

    iput v1, v0, Landroid/view/WindowManager$LayoutParams;->y:I

    .line 446
    iget-object v0, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    check-cast v0, Landroid/app/Activity;

    invoke-virtual {v0}, Landroid/app/Activity;->getWindowManager()Landroid/view/WindowManager;

    move-result-object v0

    iput-object v0, p0, Lcom/android/support/Menu;->mWindowManager:Landroid/view/WindowManager;

    .line 447
    iget-object v0, p0, Lcom/android/support/Menu;->mWindowManager:Landroid/view/WindowManager;

    iget-object v1, p0, Lcom/android/support/Menu;->rootFrame:Landroid/widget/FrameLayout;

    iget-object v2, p0, Lcom/android/support/Menu;->vmParams:Landroid/view/WindowManager$LayoutParams;

    invoke-interface {v0, v1, v2}, Landroid/view/WindowManager;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 448
    return-void
.end method

.method public SetWindowManagerWindowService()V
    .locals 7

    .line 410
    sget v0, Landroid/os/Build$VERSION;->SDK_INT:I

    const/16 v1, 0x1a

    if-lt v0, v1, :cond_0

    const/16 v0, 0x7f6

    const/16 v4, 0x7f6

    goto :goto_0

    :cond_0
    const/16 v0, 0x7d2

    const/16 v4, 0x7d2

    .line 411
    .local v4, "iparams":I
    :goto_0
    new-instance v0, Landroid/view/WindowManager$LayoutParams;

    const v5, 0x4000008

    const/4 v6, -0x3

    const/4 v2, -0x2

    const/4 v3, -0x2

    move-object v1, v0

    invoke-direct/range {v1 .. v6}, Landroid/view/WindowManager$LayoutParams;-><init>(IIIII)V

    iput-object v0, p0, Lcom/android/support/Menu;->vmParams:Landroid/view/WindowManager$LayoutParams;

    .line 418
    iget-object v0, p0, Lcom/android/support/Menu;->vmParams:Landroid/view/WindowManager$LayoutParams;

    const/16 v1, 0x33

    iput v1, v0, Landroid/view/WindowManager$LayoutParams;->gravity:I

    .line 419
    iget-object v0, p0, Lcom/android/support/Menu;->vmParams:Landroid/view/WindowManager$LayoutParams;

    iget v1, p0, Lcom/android/support/Menu;->POS_X:I

    iput v1, v0, Landroid/view/WindowManager$LayoutParams;->x:I

    .line 420
    iget-object v0, p0, Lcom/android/support/Menu;->vmParams:Landroid/view/WindowManager$LayoutParams;

    iget v1, p0, Lcom/android/support/Menu;->POS_Y:I

    iput v1, v0, Landroid/view/WindowManager$LayoutParams;->y:I

    .line 422
    iget-object v0, p0, Lcom/android/support/Menu;->getContext:Landroid/content/Context;

    const-string v1, "window"

    invoke-virtual {v0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/String;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Landroid/view/WindowManager;

    iput-object v0, p0, Lcom/android/support/Menu;->mWindowManager:Landroid/view/WindowManager;

    .line 423
    iget-object v0, p0, Lcom/android/support/Menu;->mWindowManager:Landroid/view/WindowManager;

    iget-object v1, p0, Lcom/android/support/Menu;->rootFrame:Landroid/widget/FrameLayout;

    iget-object v2, p0, Lcom/android/support/Menu;->vmParams:Landroid/view/WindowManager$LayoutParams;

    invoke-interface {v0, v1, v2}, Landroid/view/WindowManager;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V

    .line 425
    const/4 v0, 0x1

    iput-boolean v0, p0, Lcom/android/support/Menu;->overlayRequired:Z

    .line 426
    return-void
.end method

.method native SettingsList()[Ljava/lang/String;
.end method

.method public ShowMenu()V
    .locals 4

    .line 379
    iget-object v0, p0, Lcom/android/support/Menu;->rootFrame:Landroid/widget/FrameLayout;

    iget-object v1, p0, Lcom/android/support/Menu;->mRootContainer:Landroid/widget/RelativeLayout;

    invoke-virtual {v0, v1}, Landroid/widget/FrameLayout;->addView(Landroid/view/View;)V

    .line 381
    new-instance v0, Landroid/os/Handler;

    invoke-direct {v0}, Landroid/os/Handler;-><init>()V

    .line 382
    .local v0, "handler":Landroid/os/Handler;
    new-instance v1, Lcom/android/support/Menu$6;

    invoke-direct {v1, p0, v0}, Lcom/android/support/Menu$6;-><init>(Lcom/android/support/Menu;Landroid/os/Handler;)V

    const-wide/16 v2, 0x1f4

    invoke-virtual {v0, v1, v2, v3}, Landroid/os/Handler;->postDelayed(Ljava/lang/Runnable;J)Z

    .line 405
    return-void
.end method

.method public onDestroy()V
    .locals 2

    .line 1392
    iget-object v0, p0, Lcom/android/support/Menu;->rootFrame:Landroid/widget/FrameLayout;

    if-eqz v0, :cond_0

    .line 1393
    iget-object v0, p0, Lcom/android/support/Menu;->mWindowManager:Landroid/view/WindowManager;

    iget-object v1, p0, Lcom/android/support/Menu;->rootFrame:Landroid/widget/FrameLayout;

    invoke-interface {v0, v1}, Landroid/view/WindowManager;->removeView(Landroid/view/View;)V

    .line 1395
    :cond_0
    return-void
.end method

.method public setVisibility(I)V
    .locals 1
    .param p1, "view"    # I

    .line 1386
    iget-object v0, p0, Lcom/android/support/Menu;->rootFrame:Landroid/widget/FrameLayout;

    if-eqz v0, :cond_0

    .line 1387
    iget-object v0, p0, Lcom/android/support/Menu;->rootFrame:Landroid/widget/FrameLayout;

    invoke-virtual {v0, p1}, Landroid/widget/FrameLayout;->setVisibility(I)V

    .line 1389
    :cond_0
    return-void
.end method
