// Commands for sending messages to an ssd1963 lcd driver
//
// Copyright (C) 2018  Kevin O'Connor <kevin@koconnor.net>
//
// This file may be distributed under the terms of the GNU GPLv3 license.

#include "autoconf.h" // CONFIG_CLOCK_FREQ
#include "basecmd.h" // oid_alloc
#include "board/gpio.h" // gpio_out_write
#include "board/irq.h" // irq_poll
#include "board/misc.h" // timer_from_us
#include "board/internal.h" // GPIO
#include "command.h" // DECL_COMMAND
#include "sched.h" // DECL_SHUTDOWN

void enable_i8080_fsmc(uint32_t cs_pin, uint32_t rs_pin);
void i8080_fsmc_wr_reg(uint16_t cmd);
void i8080_fsmc_wr_data(uint16_t data);
uint16_t i8080_fsmc_rd_data(void);

struct i8080 {
    struct gpio_out bl;
    uint32_t cs, rs;
};


static uint32_t
nsecs_to_ticks(uint32_t ns)
{
    return timer_from_us(ns * 1000) / 1000000;
}

static inline void
ndelay(uint32_t nsecs)
{
    uint32_t end = timer_read_time() + nsecs_to_ticks(nsecs);
    while (timer_is_before(timer_read_time(), end))
        irq_poll();
}



/****************************************************************
 * Init functions
 ****************************************************************/

/* #define SSD1963_LCD_PARA */
/* #define SSD_DCLK_FREQUENCY  12  // 12Mhz */

/* #define SSD_HOR_PULSE_WIDTH 1 */
/* #define SSD_HOR_BACK_PORCH  43 */
/* #define SSD_HOR_FRONT_PORCH 2 */

/* #define SSD_VER_PULSE_WIDTH 1 */
/* #define SSD_VER_BACK_PORCH  12 */
/* #define SSD_VER_FRONT_PORCH 1 */

/* #define LCD_WIDTH   480 */
/* #define LCD_HEIGHT  272 */

/* #define SSD_HOR_RESOLUTION LCD_WIDTH   // LCD width pixel */
/* #define SSD_VER_RESOLUTION LCD_HEIGHT  // LCD height pixel */

/* #define SSD_HT  (SSD_HOR_RESOLUTION+SSD_HOR_BACK_PORCH+SSD_HOR_FRONT_PORCH) */
/* #define SSD_HPS (SSD_HOR_BACK_PORCH) */
/* #define SSD_VT  (SSD_VER_RESOLUTION+SSD_VER_BACK_PORCH+SSD_VER_FRONT_PORCH) */
/* #define SSD_VPS (SSD_VER_BACK_PORCH) */


/* void ssd1963_Init_Sequential(void) */
/*   { */
/*     uint32_t LCDC_FPR; */
/*     LCD_WR_REG(0xE2);   // Set PLL with OSC = 25MHz (hardware), 250Mhz < VC0 < 800Mhz */
/*     LCD_WR_DATA(0x17);  // M = 0x17 = 23, VCO = 25Mhz * (M + 1) = 25 * 24 = 600Mhz */
/*     LCD_WR_DATA(0x04);  // N = 0x04 = 4, PLL = VCO / (N + 1) = 600 / 5 = 120Mhz */
/*     LCD_WR_DATA(0x54);  // C[2] = 1, Effectuate the multiplier and divider value */
/*     LCD_WR_REG(0xE0);   // Start PLL command */
/*     LCD_WR_DATA(0x01);  // enable PLL */
/*     //    Delay_ms(10); */
/*     ndelay(10000); */
/*     LCD_WR_REG(0xE0);   // Start PLL command again */
/*     LCD_WR_DATA(0x03);  // now, use PLL output as system clock */
/*     //    Delay_ms(10); */
/*     ndelay(10000); */
/*     LCD_WR_REG(0x01);   // Soft reset */
/*     //    Delay_ms(100); */
/*     ndelay(100000); */
/*     LCDC_FPR = (SSD_DCLK_FREQUENCY * 1048576) / 120 -1;  // DCLK Frequency = PLL * (LCDC_FPR + 1)/1048576, LCDC_FPR = (DCLK Frequency * 1048576) / PLL - 1 */
/*     LCD_WR_REG(0xE6);   // 12Mhz = 120Mhz * (LCDC_FPR + 1)/1048576, LCDC_FPR = 104856.6 = 0x019998 */
/*     LCD_WR_DATA((LCDC_FPR >> 16) & 0xFF); */
/*     LCD_WR_DATA((LCDC_FPR >> 8) & 0xFF); */
/*     LCD_WR_DATA(LCDC_FPR & 0xFF); */
/*     LCD_WR_REG(0xB0);   // Set LCD mode */
/*     LCD_WR_DATA(0x00);  // 0x00: 16bits data, 0x20: 24bits data */
/*     LCD_WR_DATA(0x00);  // 0x00: TFT Mode */
/*     LCD_WR_DATA((SSD_HOR_RESOLUTION - 1) >> 8);  // LCD width pixel */
/*     LCD_WR_DATA((SSD_HOR_RESOLUTION - 1) & 0xFF); */
/*     LCD_WR_DATA((SSD_VER_RESOLUTION - 1) >> 8);  // LCD height pixel */
/*     LCD_WR_DATA((SSD_VER_RESOLUTION - 1) & 0xFF); */
/*     LCD_WR_DATA(0x00);  // RGB format */
/*     LCD_WR_REG(0xB4);   // Set horizontal period */
/*     LCD_WR_DATA((SSD_HT - 1) >> 8);  // Horizontal total period (display + non-display) in pixel clock */
/*     LCD_WR_DATA(SSD_HT - 1); */
/*     LCD_WR_DATA(SSD_HPS >> 8);  // Non-display period between the start of the horizontal sync (LLINE) signal and the first display data */
/*     LCD_WR_DATA(SSD_HPS); */
/*     LCD_WR_DATA(SSD_HOR_PULSE_WIDTH - 1);  // horizontal sync pulse width (LLINE) in pixel clock */
/*     LCD_WR_DATA(0x00); */
/*     LCD_WR_DATA(0x00); */
/*     LCD_WR_DATA(0x00); */
/*     LCD_WR_REG(0xB6);   // Set vertical period */
/*     LCD_WR_DATA((SSD_VT - 1) >> 8); */
/*     LCD_WR_DATA(SSD_VT - 1); */
/*     LCD_WR_DATA(SSD_VPS >> 8); */
/*     LCD_WR_DATA(SSD_VPS); */
/*     LCD_WR_DATA(SSD_VER_FRONT_PORCH - 1); */
/*     LCD_WR_DATA(0x00); */
/*     LCD_WR_DATA(0x00); */
/*     LCD_WR_REG(0xF0);   // Set pixel data interface format */
/*     LCD_WR_DATA(0x03);  // 16-bit(565 format) data for 16bpp */
/*     LCD_WR_REG(0xBC);   // postprocessor for contrast/brightness/saturation. */
/*     LCD_WR_DATA(0x34);  // Contrast value (0-127). Set to 52 to reduce banding/flickering. */
/*     LCD_WR_DATA(0x77);  // Brightness value (0-127). Set to 119 to reduce banding/flickering. */
/*     LCD_WR_DATA(0x48);  // Saturation value (0-127). */
/*     LCD_WR_DATA(0x01);  // Enable/disable the postprocessor for contrast/brightness/saturation (1-0). */
/*     LCD_WR_REG(0x29);   // Set display on */

/*     LCD_WR_REG(0x36);   // Set address mode */
/*     LCD_WR_DATA(0x00); */
/*   } */


/****************************************************************
 * Transmit functions
 ****************************************************************/

void LCD_IO_ReadCmd8MultipleData8(uint8_t Cmd, uint8_t *pData, uint32_t Size)
{
  i8080_fsmc_wr_reg(Cmd);
  while(Size--)
  {
      *pData = i8080_fsmc_rd_data();
    pData++;
  }
}

/****************************************************************
 * Interface
 ****************************************************************/

void
command_config_i8080(uint32_t *args)
{
    struct i8080 *i = oid_alloc(args[0], command_config_i8080, sizeof(*i));
    i->bl = gpio_out_setup(GPIO('D', 12), 1);
    i->cs = GPIO('D', 7);
    i->rs = GPIO('E', 2);

    enable_i8080_fsmc(i->cs, i->rs);
    //    ssd1963_LCD_GPIO_Config();
    //    ssd1963_LCD_FSMC_Config();
    //    ssd1963_Init_Sequential();
    //    GUI_Clear(WHITE);
}
DECL_COMMAND(command_config_i8080, "config_i8080 oid=%c");


    /* LCD_IO_ReadCmd8MultipleData8(0xA1, (uint8_t *)&dt, 5); */
    /* sendf("ssd1963_send_cmds_end c=%c d1=%c d2=%c d3=%c d4=%c d5=%c d6=%c d7=%c d8=%c", 0xA1, */
    /*       dt[0], dt[1], dt[2], dt[3], dt[4], 999, 999, 999); */

    /* LCD_IO_ReadCmd8MultipleData8(0xE2, (uint8_t *)&dt, 3); */
    /* sendf("ssd1963_send_cmds_end c=%c d1=%c d2=%c d3=%c d4=%c d5=%c d6=%c d7=%c d8=%c", 0xE2,  */
    /*       dt[0], dt[1], dt[2], dt[3], 999, 999, 999, 999); */

    /* LCD_IO_ReadCmd8MultipleData8(0xE7, (uint8_t *)&dt, 3); */
    /* sendf("ssd1963_send_cmds_end c=%c d1=%c d2=%c d3=%c d4=%c d5=%c d6=%c d7=%c d8=%c", 0xE7,  */
    /*       dt[0], dt[1], dt[2], 999, 999, 999, 999, 999); */

    /* LCD_IO_ReadCmd8MultipleData8(0xB1, (uint8_t *)&dt, 7); */
    /* sendf("ssd1963_send_cmds_end c=%c d1=%c d2=%c d3=%c d4=%c d5=%c d6=%c d7=%c d8=%c", 0xB1, */
    /*       dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], 999); */

    /* LCD_IO_ReadCmd8MultipleData8(0xB5, (uint8_t *)&dt, 8); */
    /* sendf("ssd1963_send_cmds_end c=%c d1=%c d2=%c d3=%c d4=%c d5=%c d6=%c d7=%c d8=%c", 0xB5,  */
    /*       dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], dt[7]); */

    /* LCD_IO_ReadCmd8MultipleData8(0xB7, (uint8_t *)&dt, 7); */
    /* sendf("ssd1963_send_cmds_end c=%c d1=%c d2=%c d3=%c d4=%c d5=%c d6=%c d7=%c d8=%c", 0xB7,  */
    /*       dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], 999); */

    /* LCD_IO_ReadCmd8MultipleData8(0xF1, (uint8_t *)&dt, 1); */
    /* sendf("ssd1963_send_cmds_end c=%c d1=%c d2=%c d3=%c d4=%c d5=%c d6=%c d7=%c d8=%c", 0xF1, */
    /*       dt[0], 999, 999, 999, 999, 999, 999, 999); */

    /* LCD_IO_ReadCmd8MultipleData8(0xBD, (uint8_t *)&dt, 4); */
    /* sendf("ssd1963_send_cmds_end c=%c d1=%c d2=%c d3=%c d4=%c d5=%c d6=%c d7=%c d8=%c", 0xBD,  */
    /*       dt[0], dt[1], dt[2], dt[3], 999, 999, 999, 999); */

void
command_i8080_read_data(uint32_t *args)
{
    uint8_t dt[8] = {0,0,0,0,0,0,0,0};
    // struct i8080 *i = oid_lookup(args[0], command_config_i8080);

    uint8_t cmd = args[1], cnt = args[2];
    LCD_IO_ReadCmd8MultipleData8(cmd, (uint8_t *)&dt, cnt);
    sendf("i8080_read_data_out c=%c d1=%c d2=%c d3=%c d4=%c d5=%c d6=%c d7=%c d8=%c", cmd,
	  dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], dt[6], dt[7]);
}
DECL_COMMAND(command_i8080_read_data, "i8080_read_data oid=%c cmd=%c cnt=%c");


void
command_i8080_send_cmd(uint32_t *args)
{
    // struct i8080 *i = oid_lookup(args[0], command_config_i8080);

    uint16_t count = args[2], *data = command_decode_ptr(args[3]);

    //    LCD_WR_REG(args[1]);
    i8080_fsmc_wr_reg(args[1]);

    while (--count) {
	/* uint16_t datum = *data++; */
	/* LCD_WR_DATA(cmd); */
	//	LCD_WR_DATA((*data++));
	i8080_fsmc_wr_data((*data++));
    }
    
    sendf("i8080_send_cmd_sent cmd=%c pcnt=%c", args[1], count);
}
DECL_COMMAND(command_i8080_send_cmd, "i8080_send_cmd oid=%c cmd=%c data=%*s");


void
command_i8080_fill(uint32_t *args)
{
    // struct i8080 *i = oid_lookup(args[0], command_config_i8080);
    uint32_t index=0;
    uint16_t fact = args[1];

    uint16_t sx = fact;
    uint16_t sy = fact;
    uint16_t ex = fact*2;
    uint16_t ey = fact*2;

    /* LCD_WR_REG(0x2A); */
    /* LCD_WR_DATA(sx>>8);LCD_WR_DATA(sx&0xFF); */
    /* LCD_WR_DATA(ex>>8);LCD_WR_DATA(ex&0xFF); */
    /* LCD_WR_REG(0x2B); */
    /* LCD_WR_DATA(sy>>8);LCD_WR_DATA(sy&0xFF); */
    /* LCD_WR_DATA(ey>>8);LCD_WR_DATA(ey&0xFF); */
    /* LCD_WR_REG(0x2C);  // Ready to write memory */
    
    i8080_fsmc_wr_reg(0x2A);
    i8080_fsmc_wr_data(sx>>8);i8080_fsmc_wr_data(sx&0xFF);
    i8080_fsmc_wr_data(ex>>8);i8080_fsmc_wr_data(ex&0xFF);
    i8080_fsmc_wr_reg(0x2B);
    i8080_fsmc_wr_data(sy>>8);i8080_fsmc_wr_data(sy&0xFF);
    i8080_fsmc_wr_data(ey>>8);i8080_fsmc_wr_data(ey&0xFF);
    i8080_fsmc_wr_reg(0x2C);  // Ready to write memory

    for (index=0; index<fact*fact; index++) {
	//	LCD_WR_DATA(0x00DF);
	//	LCD_WR_DATA(fact);
	//	LCD_WR_DATA(0x0760);
	i8080_fsmc_wr_data(0x0760);
    }
      
    sendf("i8080_fill_done");
}
DECL_COMMAND(command_i8080_fill, "i8080_fill oid=%c fact=%c");


void
i8080_shutdown(void)
{
    /* uint8_t i; */
    /* struct ssd1963 *s; */
    /* foreach_oid(i, s, command_config_ssd1963) { */
    /*     s->s1 = s->s2 = 0; */
    /* } */
}
DECL_SHUTDOWN(i8080_shutdown);
