000010 IDENTIFICATION DIVISION.                                                 
000020 PROGRAM-ID. RPDUMP.                                                      
************************************************************************        
000040* THIS PROGRAM DUMPS INTO THE DUMPMASTER                                  
************************************************************************        
***********************************************************************
RES001* CALL FAULT FINDER FOR BATCH ONLY
***********************************************************************
000090 ENVIRONMENT DIVISION.                                                    
TOFANN CONFIGURATION SECTION.
TOFANN SOURCE-COMPUTER. IBM-390.
TOFANN OBJECT-COMPUTER.
TOFANN     PROGRAM COLLATING SEQUENCE EBC.
TOFANN SPECIAL-NAMES.
TOFANN     ALPHABET EBC IS EBCDIC.
000160 DATA DIVISION.                                                           
000170 WORKING-STORAGE SECTION.                                                 
000180 77  CMS-IDENTIFICATION PIC X(8) VALUE 'RPDUMP'.                          
000190 77  CMS-ID-VALUE PIC X(44)   VALUE                                       
000200         'CMS-ID= 12May2008 19:43:35/winifred/res/V1   '.                  
000210 01 WS-ABENDCODE         PIC S9(8) COMP VALUE +1002.                      
000220 77  WS-TITLE            PIC X(80)   DISPLAY.                             
000230 77  WS-OPTIONS          PIC X(255)  VALUE 'FNAME(SYSUDUMP)'.             
000240 01  WS-USER             PIC X(32).                    
000250 01  WS-FEEDBACK-CODE    PIC X(12)   DISPLAY.          
000260 01 Z1 pic x(4) comp-5.
000270 01 Z2 pic x(4) comp-5.
000280 01 Z3 pic x(4) comp-5.                   
000290 PROCEDURE DIVISION .                                                     
000300                                                                          
000310 0000-MAIN-PARA. 
000320     DISPLAY '*** CALL RPDUMP ***'
RES001     DISPLAY "LOGNAME" UPON ENVIRONMENT-NAME
RES001     ACCEPT WS-USER FROM ENVIRONMENT-VALUE
RES001     IF WS-USER(1:4) NOT = "cics"
YDR           CALL "CBL_FFND_REPORT" using by value Z1 
YDR                               by value Z2
YDR                               returning Z3  
000390     CALL 'CEE3DMP' USING WS-TITLE WS-OPTIONS WS-FEEDBACK-CODE.           
000400     GOBACK.                                                              
